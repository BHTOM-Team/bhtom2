function dataProductSelect() {

    var photometry = document.getElementById("id_data_product_type_0").checked;
    var photometry_non_detaction = document.getElementById("id_data_product_type_1").checked;
    var fits_file = document.getElementById("id_data_product_type_2").checked;
    var spectroscopy = document.getElementById("id_data_product_type_3").checked;
    var image = document.getElementById("id_data_product_type_4").checked;

    var mjd = document.getElementById("mjd");
    var ExpTime = document.getElementById("ExpTime");
    var matchDist = document.getElementById("id_matchDist");
    var dryRun = document.getElementById("id_dryRun");
    var observatory = document.getElementById("id_observatory");
    var filter = document.getElementById("id_filter");
    var observer = document.getElementById("id_observer");
    var facility = document.getElementById("id_facility");

    if (photometry === true) {

        mjd.setAttribute("required", true);
        ExpTime.setAttribute("required", true);
        matchDist.setAttribute("required", true);
        observatory.setAttribute("required", true);
        filter.setAttribute("required", true);
        observer.removeAttribute("required");
        facility.removeAttribute("required");

        mjd.parentElement.style.display = "block";
        ExpTime.parentElement.style.display = "block";
        matchDist.parentElement.style.display = "block";
        dryRun.parentElement.style.display = "block";
        observatory.parentElement.style.display = "block";
        filter.parentElement.style.display = "block";
        observer.parentElement.style.display = "none";
        facility.parentElement.style.display = "none";

    }
    if (photometry_non_detaction === true) {

        mjd.setAttribute("required", true);
        ExpTime.setAttribute("required", true);
        matchDist.setAttribute("required", true);
        observatory.setAttribute("required", true);
        filter.setAttribute("required", true);
        observer.removeAttribute("required");
        facility.removeAttribute("required");

        mjd.parentElement.style.display = "block";
        ExpTime.parentElement.style.display = "block";
        matchDist.parentElement.style.display = "block";
        dryRun.parentElement.style.display = "block";
        observatory.parentElement.style.display = "block";
        filter.parentElement.style.display = "block";
        observer.parentElement.style.display = "none";
        facility.parentElement.style.display = "none";

    }

    if (fits_file === true) {

        mjd.removeAttribute("required");
        ExpTime.removeAttribute("required");
        matchDist.setAttribute("required", true);
        observatory.setAttribute("required", true);
        filter.setAttribute("required", true);
        observer.removeAttribute("required");
        facility.removeAttribute("required");

        mjd.parentElement.style.display = "none";
        ExpTime.parentElement.style.display = "none";
        matchDist.parentElement.style.display = "block";
        dryRun.parentElement.style.display = "block";
        observatory.parentElement.style.display = "block";
        filter.parentElement.style.display = "block";
        observer.parentElement.style.display = "none";
        facility.parentElement.style.display = "none";

    }

    if (spectroscopy === true) {

        mjd.removeAttribute("required");
        ExpTime.removeAttribute("required");
        matchDist.removeAttribute("required");
        observatory.removeAttribute("required");
        filter.removeAttribute("required");
        observer.setAttribute("required", true);
        facility.setAttribute("required", true);

        mjd.parentElement.style.display = "none";
        ExpTime.parentElement.style.display = "none";
        matchDist.parentElement.style.display = "none";
        dryRun.parentElement.style.display = "none";
        observatory.parentElement.style.display = "none";
        filter.parentElement.style.display = "none";
        observer.parentElement.style.display = "block";
        facility.parentElement.style.display = "block";

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