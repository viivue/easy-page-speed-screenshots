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
    options.style.display = checkbox.checked ? 'flex' : 'none';

    // Handle checkbox toggle
    checkbox.addEventListener('change', async function(){
        options.style.display = this.checked ? 'flex' : 'none';
    });
});