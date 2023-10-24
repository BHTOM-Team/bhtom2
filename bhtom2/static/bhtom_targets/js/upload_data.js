function dataProductSelect() {

    var photometry = document.getElementById("id_data_product_type_0").checked;
    var photometry_non_detaction = document.getElementById("id_data_product_type_1").checked;
    var fits_file = document.getElementById("id_data_product_type_2").checked;
    var spectroscopy = document.getElementById("id_data_product_type_3").checked;
    // var image = document.getElementById("id_data_product_type_4").checked;

    var mjd = document.getElementById("mjd");
    var dryRun = document.getElementById("id_dryRun");
    var observatory = document.getElementById("id_observatory");
    var filter = document.getElementById("id_filter");
    var observer = document.getElementById("id_observer");

    if (photometry === true) {

        mjd.setAttribute("required", true);
        observatory.setAttribute("required", true);
        filter.setAttribute("required", true);
        observer.setAttribute("required", true);

        mjd.parentElement.style.display = "block";
        dryRun.parentElement.style.display = "block";
        observatory.parentElement.style.display = "block";
        filter.parentElement.style.display = "block";
        observer.parentElement.style.display = "block";
    } 
    if (photometry_non_detaction === true) {
        mjd.setAttribute("required", true);
        observatory.setAttribute("required", true);
        filter.setAttribute("required", true);
        observer.setAttribute("required", true);

        mjd.parentElement.style.display = "block";
        dryRun.parentElement.style.display = "block";
        observatory.parentElement.style.display = "block";
        filter.parentElement.style.display = "block";
        observer.parentElement.style.display = "block";
    }

    if (fits_file === true) {

        observatory.setAttribute("required", true);
        filter.setAttribute("required", true);
        observer.removeAttribute("required");
        mjd.removeAttribute("required");

        mjd.parentElement.style.display = "none";
        dryRun.parentElement.style.display = "block";
        observatory.parentElement.style.display = "block";
        filter.parentElement.style.display = "block";
        observer.parentElement.style.display = "block";
    }

    if (spectroscopy === true) {
        observer.setAttribute("required",true);
        observatory.removeAttribute("required");
        filter.removeAttribute("required");
        mjd.removeAttribute("required");
        dryRun.removeAttribute("required");

        mjd.parentElement.style.display = "none";
        dryRun.parentElement.style.display = "none";
        observatory.parentElement.style.display = "none";
        filter.parentElement.style.display = "none";
        observer.parentElement.style.display = "block";

    }

    // if (data_type_photometry_asas === true) {

    //     mjd.removeAttribute("required");
    //     ExpTime.removeAttribute("required");
    //     matchDist.removeAttribute("required");
    //     observatory.removeAttribute("required");
    //     filter.removeAttribute("required");
    //     observer.removeAttribute("required");
    //     facility.removeAttribute("required");

    //     mjd.parentElement.style.display = "none";
    //     ExpTime.parentElement.style.display = "none";
    //     matchDist.parentElement.style.display = "none";
    //     dryRun.parentElement.style.display = "none";
    //     observatory.parentElement.style.display = "none";
    //     filter.parentElement.style.display = "none";
    //     observer.parentElement.style.display = "none";
    //     facility.parentElement.style.display = "none";

    // }

}

