function toggleGTMetrixKey() {
    const checkbox = document.getElementById('gtmetrix-checkbox');
    const keyContainer = document.getElementById('gtmetrix-key-container');

    if (checkbox.checked) {
        keyContainer.classList.add('visible');
    } else {
        keyContainer.classList.remove('visible');
    }
}