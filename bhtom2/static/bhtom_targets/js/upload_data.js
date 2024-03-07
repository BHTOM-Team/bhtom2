function dataProductSelect() {

    var photometry = document.getElementById("id_data_product_type_0").checked;
    var photometry_csv = document.getElementById("id_data_product_type_1").checked;
    var fits_file = document.getElementById("id_data_product_type_2").checked;
    var spectroscopy = document.getElementById("id_data_product_type_3").checked;

    var mjd = document.getElementById("mjd");
    var dryRun = document.getElementById("id_dryRun");
    var observatory = document.getElementById("id_observatory");
    var observatory_input = document.getElementById("id_observatory_input"); // input text for spectroscopy and photometry csv
    var camera = document.getElementById("id_camera");
    var filter = document.getElementById("id_filter");
    var observer = document.getElementById("id_observer");

    if (photometry === true) {

        mjd.setAttribute("required", true);
        observatory.setAttribute("required", true);
        camera.setAttribute("required", true);
        filter.setAttribute("required", true);
        observer.setAttribute("required", true);

        observatory_input.removeAttribute("required");

        mjd.parentElement.style.display = "block";
        dryRun.parentElement.style.display = "block";
        observatory.parentElement.style.display = "block";
        camera.parentElement.style.display = "block";
        filter.parentElement.style.display = "block";
        observer.parentElement.style.display = "block";
        observatory_input.parentElement.style.display = "none";
    } 
    if (fits_file === true) {

        observatory.setAttribute("required", true);
        camera.setAttribute("required", true);
        filter.setAttribute("required", true);
        observer.setAttribute("required", true);
        mjd.removeAttribute("required");
        observatory_input.removeAttribute("required");

        mjd.parentElement.style.display = "none";
        dryRun.parentElement.style.display = "block";
        observatory.parentElement.style.display = "block";
        camera.parentElement.style.display = "block";
        filter.parentElement.style.display = "block";
        observer.parentElement.style.display = "block";
        observatory_input.parentElement.style.display = "none";
    }

    if (spectroscopy === true || photometry_csv ) {
        observer.setAttribute("required",true);
        observatory_input.setAttribute("required",true);
        observatory.removeAttribute("required");
        camera.removeAttribute("required");
        filter.removeAttribute("required");
        mjd.removeAttribute("required");
        dryRun.removeAttribute("required");
        

        mjd.parentElement.style.display = "none";
        dryRun.parentElement.style.display = "none";
        observatory.parentElement.style.display = "none";
        camera.parentElement.style.display = "none";
        filter.parentElement.style.display = "none";
        observatory_input.parentElement.style.display = "block";
        observer.parentElement.style.display = "block";

    }
}

