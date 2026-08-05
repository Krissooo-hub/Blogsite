let isAnimating = false;

function swipeCard() {
    if (isAnimating) return;

    const cardStack = document.getElementById('cardStack');
    if (!cardStack) return;

    const cards = Array.from(cardStack.querySelectorAll('.card'));
    if (cards.length <= 1) return; // No rotation needed if 1 or 0 cards

    const topCard = cardStack.querySelector('.card-1');
    if (!topCard) return;

    isAnimating = true;

    // 1. Trigger swipe-out animation on the top card
    topCard.classList.add('swiping');

    setTimeout(() => {
        const totalCards = cards.length;
        topCard.classList.remove('swiping');

        // 2. Rotate class indices dynamically (card-1 -> card-N, card-2 -> card-1, etc.)
        cards.forEach(card => {
            const match = card.className.match(/card-(\d+)/);
            if (match) {
                let currentNum = parseInt(match[1]);
                let newNum = (currentNum === 1) ? totalCards : currentNum - 1;
                card.className = `card card-${newNum}`;
            }
        });

        // 3. Get the new top card (.card-1) and update the adjacent text card
        const newTopCard = cardStack.querySelector('.card-1');
        const titleElement = document.getElementById('projectTitle');
        const captionElement = document.getElementById('projectCaption');

        if (newTopCard) {
            const title = newTopCard.getAttribute('data-title') || 'My Projects';
            const caption = newTopCard.getAttribute('data-caption') || '';

            if (titleElement) titleElement.textContent = title;
            if (captionElement) captionElement.textContent = caption;
        }

        isAnimating = false;
    }, 500); // 500ms matches your CSS animation duration
}

// Auto-swipe functionality for interest cards (Music, Games, Lifestyle)
// Sync image swiping with dynamic text updates
document.addEventListener('DOMContentLoaded', () => {
    const carousels = document.querySelectorAll('.auto-carousel');

    carousels.forEach(carousel => {
        const images = carousel.querySelectorAll('.carousel-images img');
        const titleEl = carousel.querySelector('.dynamic-title');
        const captionEl = carousel.querySelector('.dynamic-caption');
        const intervalTime = parseInt(carousel.getAttribute('data-interval')) || 4000;

        if (images.length === 0 || !titleEl || !captionEl) return;

        let currentIndex = 0;

        setInterval(() => {
            // Remove active class from current image
            images[currentIndex].classList.remove('active');

            // Advance to next image index
            currentIndex = (currentIndex + 1) % images.length;

            const nextImg = images[currentIndex];
            nextImg.classList.add('active');

            // Dynamically sync text with the active image's dataset attributes
            titleEl.textContent = nextImg.getAttribute('data-title') || '';
            captionEl.textContent = nextImg.getAttribute('data-caption') || '';

        }, intervalTime);
    });
});