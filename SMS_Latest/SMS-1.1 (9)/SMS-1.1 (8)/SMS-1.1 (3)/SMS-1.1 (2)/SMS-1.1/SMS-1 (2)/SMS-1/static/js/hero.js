// Hero section animations and effects
document.addEventListener('DOMContentLoaded', function() {
    // Simple animation for hero section elements
    const heroTitle = document.querySelector('.hero-section h1');
    const heroSubtitle = document.querySelector('.hero-section .lead');
    const heroDescription = document.querySelector('.hero-section p:not(.lead)');
    const heroButton = document.querySelector('.hero-section .btn');
    
    if (heroTitle) {
        heroTitle.style.opacity = '0';
        heroTitle.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            heroTitle.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
            heroTitle.style.opacity = '1';
            heroTitle.style.transform = 'translateY(0)';
        }, 300);
    }
    
    if (heroSubtitle) {
        heroSubtitle.style.opacity = '0';
        heroSubtitle.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            heroSubtitle.style.transition = 'opacity 0.8s ease 0.2s, transform 0.8s ease 0.2s';
            heroSubtitle.style.opacity = '1';
            heroSubtitle.style.transform = 'translateY(0)';
        }, 500);
    }
    
    if (heroDescription) {
        heroDescription.style.opacity = '0';
        heroDescription.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            heroDescription.style.transition = 'opacity 0.8s ease 0.4s, transform 0.8s ease 0.4s';
            heroDescription.style.opacity = '1';
            heroDescription.style.transform = 'translateY(0)';
        }, 700);
    }
    
    if (heroButton) {
        heroButton.style.opacity = '0';
        heroButton.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            heroButton.style.transition = 'opacity 0.8s ease 0.6s, transform 0.8s ease 0.6s';
            heroButton.style.opacity = '1';
            heroButton.style.transform = 'translateY(0)';
        }, 900);
    }
    
    // Parallax effect for hero background
    window.addEventListener('scroll', function() {
        const scrollPosition = window.pageYOffset;
        const heroSection = document.querySelector('.hero-section');
        
        if (heroSection) {
            heroSection.style.backgroundPosition = `center ${scrollPosition * 0.5}px`;
        }
    });
    
    // Particle effect for hero section (simple implementation)
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        // Create a few floating particles
        for (let i = 0; i < 15; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = `${Math.random() * 100}%`;
            particle.style.top = `${Math.random() * 100}%`;
            particle.style.width = `${Math.random() * 10 + 2}px`;
            particle.style.height = particle.style.width;
            particle.style.opacity = Math.random() * 0.5 + 0.1;
            particle.style.animationDuration = `${Math.random() * 10 + 10}s`;
            particle.style.animationDelay = `${Math.random() * 5}s`;
            
            heroSection.appendChild(particle);
        }
    }
});