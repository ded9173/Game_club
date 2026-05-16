document.addEventListener('DOMContentLoaded', function () {
    const piece = document.getElementById('puzzlePiece');
    const canvas = document.getElementById('puzzleCanvas');
    const ctx = canvas.getContext('2d');
    const hiddenInput = document.getElementById('puzzleX');

    const bgImageB64 = window.bgImageB64;
    const sliceWidth = window.sliceWidth;
    const maxWidth = window.maxWidth;

    const bgImage = new Image();
    bgImage.onload = function () {
        ctx.drawImage(bgImage, 0, 0);
    };
    bgImage.src = 'data:image/png;base64,' + bgImageB64;

    let isDragging = false;
    let offsetX = 0;

    piece.addEventListener('mousedown', (e) => {
        isDragging = true;
        offsetX = e.clientX - piece.getBoundingClientRect().left;
        piece.style.zIndex = 11;
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const rect = canvas.getBoundingClientRect();
        let left = e.clientX - rect.left - offsetX;
        left = Math.max(0, Math.min(left, maxWidth - sliceWidth));
        piece.style.left = left + 'px';
        hiddenInput.value = Math.round(left);
    });

    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            piece.style.zIndex = 10;
        }
    });

    // Тач-устройства
    piece.addEventListener('touchstart', (e) => {
        isDragging = true;
        const touch = e.touches[0];
        offsetX = touch.clientX - piece.getBoundingClientRect().left;
        piece.style.zIndex = 11;
        e.preventDefault();
    });

    document.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        const touch = e.touches[0];
        const rect = canvas.getBoundingClientRect();
        let left = touch.clientX - rect.left - offsetX;
        left = Math.max(0, Math.min(left, maxWidth - sliceWidth));
        piece.style.left = left + 'px';
        hiddenInput.value = Math.round(left);
        e.preventDefault();
    });

    document.addEventListener('touchend', () => {
        if (isDragging) {
            isDragging = false;
            piece.style.zIndex = 10;
        }
    });
});