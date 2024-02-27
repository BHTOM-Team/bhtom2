$(document).ready(function() {
    // Function to add a new camera form
    function addCameraForm() {
        var cameraForm = $(".camera-form:first").clone(true);
        var totalForms = $('#id_camera_set-TOTAL_FORMS');
        var formIdx = parseInt(totalForms.val());

        // Clear all input fields
        cameraForm.find("input[type='text'], input[type='number'], input[type='file']").val("");
        
        // Update the names and IDs of the cloned fields
        cameraForm.find("input[type='text'], input[type='number'], input[type='file']").each(function() {
            var field = $(this);
            var fieldName = field.attr('name');
            var fieldId = field.attr('id');
            var newFieldName = fieldName.replace(/-\d+-/g, '-' + formIdx + '-');
            var newFieldId = fieldId.replace(/-\d+/g, '-' + formIdx);
            field.attr('name', newFieldName);
            field.attr('id', newFieldId);
        });
        
        // Insert the cloned form after the last camera form
        cameraForm.insertAfter(".camera-form:last");
        
        // Add a line separator after the cloned form
        $("<div class='line-separator'></div>").insertAfter(cameraForm);

        // Increment the total forms count
        totalForms.val(formIdx + 1);
    }

    function toggleCameraFields() {
      var calibrationFlag = document.getElementById('id_calibration_flg');
      var addButton = document.getElementById('add-camera')
      var camera_fields = document.getElementById('camera-fields')
      $(".camera-form").each(function() {
        var cameraFields = $(this).find('input[type="text"], input[type="number"], input[type="file"]');

        
        if(addButton){
            if(calibrationFlag.checked){
              addButton.disabled = true;
            }
            else{
              addButton.disabled = false;
            }
        }

        if(camera_fields){
          if(calibrationFlag.checked){
            camera_fields.style.display = 'none'
          }
          else{
            camera_fields.style.display = 'block'
          }
        }
        for (var i = 0; i < cameraFields.length; i++) {
          if (calibrationFlag.checked) {
            cameraFields[i].removeAttribute('required');
          } else {
            cameraFields[i].setAttribute('required', true);
          }
        }
        

      });
    }
    

    function toggleObservatoryFields() {
      var calibrationFlag = document.getElementById('id_calibration_flg');
      var observatoryFields = [
          { id: 'id_approx_lim_mag', label: 'Approx. limit magnitude in V band* [mag]' },
          { id: 'id_filters', label: 'Filters*' },
          // { id: 'id_altitude', label: 'Altitude [m]*' },
          // { id: 'id_aperture', label: 'Aperture [m]' },
          // { id: 'id_focal_length', label: 'Focal length [mm]' },
          // { id: 'id_telescope', label: 'Telescope name' },
          // { id: 'id_comment', label: 'Comments (e.g. hyperlink to the observatory website, camera specifications, telescope info)' }
      ];
  
      observatoryFields.forEach(function(field) {
          var inputField = document.getElementById(field.id);
          var label = document.querySelector('label[for="' + field.id + '"]');
  
          if (calibrationFlag.checked) {
              label.style.display = 'none'; 
              inputField.style.display = 'none'; 
              inputField.removeAttribute('required');
          } else {
              inputField.style.display = 'block'; 
              label.style.display = 'block'; 
              if (field.id !== 'id_aperture' && field.id !== 'id_focal_length' && field.id !== 'id_telescope' && field.id !== 'id_comment') {
                  inputField.setAttribute('required', true);
              }
          }
      });
  }
  
    
    function toggleFields() {
      toggleCameraFields();
      toggleObservatoryFields();
    }

    // Add event listener to calibration flag
    document.getElementById('id_calibration_flg').addEventListener('change', toggleFields);

    // Event listener to add a new camera form
    $("#add-camera").click(function() {
        addCameraForm();
    });

    // Call toggle function on document ready
    toggleFields();
  });