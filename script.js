const form = document.getElementById('videoForm');
const promptInput = document.getElementById('prompt');
const styleSelect = document.getElementById('style');
const durationInput = document.getElementById('duration');
const durationValue = document.getElementById('durationValue');
const loading = document.getElementById('loading');
const result = document.getElementById('result');
const videoPlayer = document.getElementById('videoPlayer');
const previewBtn = document.getElementById('previewBtn');
const downloadBtn = document.getElementById('downloadBtn');
const generateBtn = document.getElementById('generateBtn');

function updateDurationText() {
  durationValue.textContent = `${durationInput.value} sec`;
}

durationInput.addEventListener('input', updateDurationText);
updateDurationText();

async function generateVideo(event) {
  event.preventDefault();

  const prompt = promptInput.value.trim();
  const style = styleSelect.value;
  const duration = Number(durationInput.value);

  if (!prompt) {
    alert('Please enter a prompt first.');
    return;
  }

  form.classList.add('hidden');
  loading.classList.remove('hidden');
  generateBtn.disabled = true;

  try {
    const response = await fetch('/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt,
        style,
        duration,
      }),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Video generation failed.');
    }

    const videoUrl = data.video_url;
    const fileName = data.filename;

    videoPlayer.src = videoUrl;
    videoPlayer.load();

    downloadBtn.href = videoUrl;
    downloadBtn.setAttribute('download', fileName);
    downloadBtn.setAttribute('title', `Download ${fileName}`);

    loading.classList.add('hidden');
    result.classList.remove('hidden');
    form.classList.remove('hidden');
    generateBtn.disabled = false;
  } catch (error) {
    loading.classList.add('hidden');
    form.classList.remove('hidden');
    generateBtn.disabled = false;
    alert(error.message || 'Something went wrong.');
  }
}

previewBtn.addEventListener('click', () => {
  if (videoPlayer.src) {
    videoPlayer.play();
  }
});

form.addEventListener('submit', generateVideo);
