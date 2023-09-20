function CheckCalibrationFlag() {
    var calibration_flg = document.getElementById("id_calibration_flg").checked;
    var name_obs = document.getElementById("id_name");
    var lon = document.getElementById("id_lon");
    var lat = document.getElementById("id_lat");

    var example_file = document.getElementById("id_example_file")
    var gain = document.getElementById("id_gain")
    var readout_noise = document.getElementById("id_readout_noise")
    var binning = document.getElementById("id_binning")
    var saturation_level = document.getElementById("id_saturation_level")

    var pixel_scale = document.getElementById("id_pixel_scale");
    var readout_speed = document.getElementById("id_readout_speed");
    var pixel_size = document.getElementById("id_pixel_size");
    var approx_lim_mag = document.getElementById("id_approx_lim_mag");
    var altitude = document.getElementById("id_altitude");
    var filters = document.getElementById("id_filters");
    var comment = document.getElementById("id_comment");

    if (calibration_flg === true) {

        name_obs.setAttribute("required", true);
        lon.setAttribute("required", true);
        lat.setAttribute("required", true);
        example_file.removeAttribute("required");
        gain.removeAttribute("required");
        readout_noise.removeAttribute("required");
        binning.removeAttribute("required");
        saturation_level.removeAttribute("required");
        pixel_scale.removeAttribute("required");
        readout_speed.removeAttribute("required");
        pixel_size.removeAttribute("required");
        approx_lim_mag.removeAttribute("required");
        filters.removeAttribute("required");
        altitude.removeAttribute("required");

        example_file.parentElement.style.display = "none";
        gain.parentElement.style.display = "none";
        readout_noise.parentElement.style.display = "none";
        binning.parentElement.style.display = "none";
        saturation_level.parentElement.style.display = "none";
        pixel_scale.parentElement.style.display = "none";
        readout_speed.parentElement.style.display = "none";
        pixel_size.parentElement.style.display = "none";
        approx_lim_mag.parentElement.style.display = "none";
        filters.parentElement.style.display = "none";
        altitude.parentElement.style.display = "none";
        comment.parentElement.style.display = "none";
    }
    else {

        name_obs.setAttribute("required", true);
        lon.setAttribute("required", true);
        lat.setAttribute("required", true);
        example_file.setAttribute("required", true);
        gain.setAttribute("required", true);
        readout_noise.setAttribute("required", true);
        binning.setAttribute("required", true);
        saturation_level.setAttribute("required", true);
        pixel_scale.setAttribute("required", true);
        readout_speed.setAttribute("required", true);
        pixel_size.setAttribute("required", true);
        approx_lim_mag.setAttribute("required", true);
        filters.setAttribute("required", true);
        altitude.setAttribute("required", true);

        example_file.parentElement.style.display = "block";
        gain.parentElement.style.display = "block";
        readout_noise.parentElement.style.display = "block";
        binning.parentElement.style.display = "block";
        saturation_level.parentElement.style.display = "block";
        pixel_scale.parentElement.style.display = "block";
        readout_speed.parentElement.style.display = "block";
        pixel_size.parentElement.style.display = "block";
        approx_lim_mag.parentElement.style.display = "block";
        filters.parentElement.style.display = "block";
        altitude.parentElement.style.display = "block";
        comment.parentElement.style.display = "block";
    }
}