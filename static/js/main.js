const FPS = 25;
let globalTimings = [];
let logInterval;

function startLogPolling() {
    const logOut = document.getElementById('log-output');
    logInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/logs');
            const data = await res.json();
            if (data.logs && logOut.textContent !== data.logs) {
                logOut.textContent = data.logs;
                logOut.scrollTop = logOut.scrollHeight;
            }
        } catch (e) {}
    }, 1000);
}

function stopLogPolling() {
    if (logInterval) clearInterval(logInterval);
}

document.addEventListener('DOMContentLoaded', () => {
    const btnAlign = document.getElementById('btn-align');
    const btnExport = document.getElementById('btn-export');
    const statusMsg = document.getElementById('status-message');
    const slidesList = document.getElementById('slides-list');
    const audioPlayer = document.getElementById('audio-player');
    const slideImg = document.getElementById('current-slide-img');

    btnAlign.addEventListener('click', async () => {
        btnAlign.disabled = true;
        btnExport.disabled = true;
        statusMsg.innerHTML = "Processing AI alignment... This may take a minute depending on the presentation length.";
        slidesList.innerHTML = "<p>Loading...</p>";
        startLogPolling();

        try {
            const response = await fetch('/api/align', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                globalTimings = data.timings;
                // Pre-select option index 0 for all
                globalTimings.forEach(t => t.selected_option_index = 0);
                
                renderSlidesList();
                updateSlidePreview();
                statusMsg.innerHTML = "Alignment complete! Review the timings on the right. You can select alternative AI guesses if needed.";
                btnExport.disabled = false;
            } else {
                statusMsg.innerHTML = `<span style="color:red">Error: ${data.error}</span>`;
            }
        } catch (err) {
            statusMsg.innerHTML = `<span style="color:red">Error: ${err.message}</span>`;
        } finally {
            btnAlign.disabled = false;
            stopLogPolling();
            // Do one last fetch to get the final logs
            fetch('/api/logs').then(r=>r.json()).then(d=>{
                document.getElementById('log-output').textContent = d.logs;
            });
        }
    });

    btnExport.addEventListener('click', async () => {
        btnExport.disabled = true;
        statusMsg.innerHTML = "Exporting FCP XML...";
        
        // Compute final start/end frames based on selected options to ensure contiguity
        const finalTimings = [];
        for (let i = 0; i < globalTimings.length; i++) {
            const slide = globalTimings[i];
            const selIdx = slide.selected_option_index;
            const startSec = slide.options[selIdx].time;
            const startFrame = Math.round(startSec * FPS);
            
            // End frame is the start frame of the NEXT slide, or end of audio
            let endFrame = startFrame + (5 * FPS); // fallback
            if (i < globalTimings.length - 1) {
                const nextSlide = globalTimings[i+1];
                const nextSelIdx = nextSlide.selected_option_index;
                const nextStartSec = nextSlide.options[nextSelIdx].time;
                endFrame = Math.round(nextStartSec * FPS);
            } else {
                // Last slide goes to end of audio (approx)
                if (audioPlayer && audioPlayer.duration) {
                    endFrame = Math.round(audioPlayer.duration * FPS);
                } else {
                    endFrame = startFrame + (10 * FPS);
                }
            }
            
            finalTimings.push({
                name: slide.name,
                start_frame: startFrame,
                end_frame: endFrame
            });
        }

        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ timings: finalTimings })
            });
            const data = await response.json();

            if (data.success) {
                statusMsg.innerHTML = `<span style="color:green">Success! ${data.message}</span>`;
            } else {
                statusMsg.innerHTML = `<span style="color:red">Error: ${data.error}</span>`;
            }
        } catch (err) {
            statusMsg.innerHTML = `<span style="color:red">Error: ${err.message}</span>`;
        } finally {
            btnExport.disabled = false;
        }
    });

    if (audioPlayer) {
        audioPlayer.addEventListener('timeupdate', () => {
            updateSlidePreview();
            highlightCurrentSlideItem();
        });

        // Custom Subtitle Rendering
        const subtitleOverlay = document.getElementById('subtitle-overlay');
        const tracks = audioPlayer.textTracks;
        if (tracks && tracks.length > 0) {
            const track = tracks[0];
            // Hide the native CC if the browser tries to render it, since we'll draw it ourselves
            track.mode = 'hidden';
            
            track.oncuechange = () => {
                const activeCues = track.activeCues;
                if (activeCues && activeCues.length > 0) {
                    // Combine all active cues (sometimes there are multiple overlapping ones)
                    let text = '';
                    for (let i = 0; i < activeCues.length; i++) {
                        text += activeCues[i].text + '<br>';
                    }
                    subtitleOverlay.innerHTML = text;
                } else {
                    subtitleOverlay.innerHTML = '';
                }
            };
        }
    }

    function formatTime(seconds) {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = Math.floor(seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    }

    function renderSlidesList() {
        slidesList.innerHTML = '';
        globalTimings.forEach((slide, slideIndex) => {
            const div = document.createElement('div');
            div.className = 'slide-item';
            div.id = `slide-item-${slideIndex}`;
            
            const selIdx = slide.selected_option_index;
            const currentStart = slide.options[selIdx].time;
            
            let html = `
                <div class="slide-header">
                    <span class="slide-name">${slide.name}</span>
                    <span class="slide-time" id="time-${slideIndex}">${formatTime(currentStart)}</span>
                </div>
            `;
            
            if (slide.notes) {
                html += `<div class="note-box">💡 <strong>AI Note:</strong> ${slide.notes}</div>`;
            }
            
            html += `<div class="options-list">`;
            slide.options.forEach((opt, optIndex) => {
                const isChecked = optIndex === selIdx ? 'checked' : '';
                html += `
                    <div class="option-item">
                        <input type="radio" name="slide-${slideIndex}" id="s${slideIndex}o${optIndex}" value="${optIndex}" ${isChecked}>
                        <label for="s${slideIndex}o${optIndex}">
                            <strong>${formatTime(opt.time)}</strong> - ${opt.reason}
                        </label>
                    </div>
                `;
            });
            html += `</div>`;
            
            div.innerHTML = html;
            slidesList.appendChild(div);
            
            // Add listeners to radios
            const radios = div.querySelectorAll('input[type="radio"]');
            radios.forEach(radio => {
                radio.addEventListener('change', (e) => {
                    slide.selected_option_index = parseInt(e.target.value);
                    const newTime = slide.options[slide.selected_option_index].time;
                    document.getElementById(`time-${slideIndex}`).innerText = formatTime(newTime);
                    // Also jump audio to this time
                    if (audioPlayer) {
                        audioPlayer.currentTime = newTime;
                        audioPlayer.play();
                    }
                    updateSlidePreview();
                });
            });
        });
    }

    function getCurrentSlideIndex() {
        if (!globalTimings.length || !audioPlayer) return -1;
        const currentTime = audioPlayer.currentTime;
        
        let currentIndex = 0;
        for (let i = 0; i < globalTimings.length; i++) {
            const selIdx = globalTimings[i].selected_option_index;
            const startSec = globalTimings[i].options[selIdx].time;
            if (currentTime >= startSec) {
                currentIndex = i;
            } else {
                break;
            }
        }
        return currentIndex;
    }

    function updateSlidePreview() {
        const idx = getCurrentSlideIndex();
        if (idx !== -1) {
            const slideName = globalTimings[idx].name;
            const src = `/media/slides/${slideName}`;
            if (slideImg.getAttribute('src') !== src) {
                slideImg.setAttribute('src', src);
            }
        }
    }

    function highlightCurrentSlideItem() {
        const idx = getCurrentSlideIndex();
        document.querySelectorAll('.slide-item').forEach((item, i) => {
            if (i === idx) {
                item.classList.add('active');
                // Optional: scroll into view
                // item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                item.classList.remove('active');
            }
        });
    }
});
