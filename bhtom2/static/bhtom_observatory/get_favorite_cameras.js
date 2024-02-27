document.addEventListener('DOMContentLoaded', function() {
    var observatorySelect = document.getElementById('id_observatory');
    var cameraSelect = document.getElementById('id_camera');
    var cameraLabel = document.querySelector('label[for="id_camera"]'); // Get the label element for id_camera

    cameraSelect.style.display = 'none'; // Hide the select element
    cameraLabel.style.display = 'none'; // Hide the label

    observatorySelect.addEventListener('change', function() {
        var observatoryId = this.value;
        if (observatoryId) {
            fetchCameras(observatoryId, userId);
            cameraSelect.style.display = 'block'; // Show the select element
            cameraLabel.style.display = 'block'; // Show the label
        } else {
            cameraSelect.style.display = 'none'; // Hide the select element
            cameraLabel.style.display = 'none'; // Hide the label
        }
    });

    function fetchCameras(observatoryId, userId) {
        fetch(window.location.origin + '/observatory/get-favorite-cameras/' + observatoryId + '/' + userId)
            .then(response => response.json())
            .then(data => {
                cameraSelect.innerHTML = ''; 
                data.forEach(camera => {
                    var option = document.createElement('option');
                    option.value = camera.id;
                    option.textContent = camera.camera_name;
                    cameraSelect.appendChild(option);
                });
            })
            .catch(error => console.error('Error fetching cameras:', error));
    }
});
