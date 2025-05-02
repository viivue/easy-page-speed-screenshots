document.addEventListener('DOMContentLoaded', function(){
    const checkbox = document.getElementById('gtmetrix-checkbox');
    const options = document.getElementById('gtmetrix-options');
    const apiKeyInput = document.getElementById('gtmetrix-key');
    const locationSelect = document.getElementById('gtmetrix-location');

    if(!checkbox || !options || !apiKeyInput || !locationSelect){
        console.error('Required GTMetrix elements not found');
        return;
    }

    // Set initial state
    options.style.opacity = checkbox.checked ? '1' : '0';

    // Handle checkbox toggle
    checkbox.addEventListener('change', async function(){
        options.style.opacity = this.checked ? '1' : '0';
    });
});

function toggleHowItWorks() {
    const content = document.getElementById('howItWorksContent');
    const icon = document.querySelector('.toggle-icon');
    const button = document.querySelector('.toggle-btn');

    if (content.style.maxHeight && content.style.maxHeight !== '0px') {
        content.style.maxHeight = '0px';
        icon.classList.remove('expanded');
        button.setAttribute('aria-expanded', 'false');
    } else {
        content.style.maxHeight = content.scrollHeight + 'px';
        icon.classList.add('expanded');
        button.setAttribute('aria-expanded', 'true');
    }
}