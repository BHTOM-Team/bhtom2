window.addEventListener("load", function () {
    CheckCalibrationFlag(); // Initial check based on calibration_flag value

    // Listen for changes in the calibration_flag checkbox
    var calibrationFlagCheckbox = document.getElementById("id_calibration_flag");
    calibrationFlagCheckbox.addEventListener("change", function () {
        CheckCalibrationFlag(); // Check whenever calibration_flag changes
    });
});


function CheckCalibrationFlag() {
    var calibration_flg = document.getElementById("id_calibration_flg").checked;
    var fieldsToToggle = ["alias-form-container"];

    // Loop through the fields and set "required" and visibility accordingly
    fieldsToToggle.forEach(function (fieldId) {
        field.parentElement.style.display = isRequired ? "block" : "none";
    });

    // Hide or show the comment field based on calibration flag
    var comment = document.getElementById("id_comment");
    comment.parentElement.style.display = calibration_flg ? "none" : "block";
}