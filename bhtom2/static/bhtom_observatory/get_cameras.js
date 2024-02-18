document.addEventListener('DOMContentLoaded', function() {
      var observatorySelect = document.getElementById('id_observatory');
      var cameraSelect = document.getElementById('id_camera');

      cameraSelect.style.display = 'none';
      
      observatorySelect.addEventListener('change', function() {
          var observatoryId = this.value;
          if (observatoryId) {
              fetchCameras(observatoryId, userId);
              cameraSelect.style.display = 'block';
          } else {
              cameraSelect.style.display = 'none'; 
          }
      });
  
      function fetchCameras(observatoryId, userId) {
          fetch(window.location.origin + '/observatory/get-cameras/' + observatoryId + '/' + userId)
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
