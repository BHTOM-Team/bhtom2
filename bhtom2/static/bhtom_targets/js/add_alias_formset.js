let aliasForm = document.querySelectorAll(".alias-formset")
let btnDelete = document.querySelectorAll(".btn-delete")
let container = document.querySelector("#alias-form-container")
let addButton = document.querySelector("#add-alias-form")
let totalForms = document.querySelector("#id_aliases-TOTAL_FORMS")

let formNum = aliasForm.length-1

addButton.addEventListener('click', addForm)
btnDelete.forEach(addCallback)

function addCallback(element) {
    element.addEventListener('click', deleteRow)
}

function deleteRow(e) {
    e.preventDefault()

    if (aliasForm.length>1) {
        container.removeChild(e.target.closest('.alias-formset'))

        aliasForm = document.querySelectorAll(".alias-formset")
        btnDelete = document.querySelectorAll(".btn-delete")

        totalForms.setAttribute('value', `${aliasForm.length}`)
        btnDelete.forEach(addCallback)
    }
}

function addForm(e) {
    e.preventDefault()

    let newForm = aliasForm[0].cloneNode(true) //Clone the bird form
    let formRegex = RegExp(`form-(\\d){1}-`,'g') //Regex to find all instances of the form number

    formNum++ //Increment the form number

    newForm.innerHTML = newForm.innerHTML.replace(formRegex, `form-${formNum}-`) //Update the new form to have the correct form number
    container.insertBefore(newForm, addButton) //Insert the new form at the end of the list of forms

    aliasForm = document.querySelectorAll(".alias-formset")
    btnDelete = document.querySelectorAll(".btn-delete")

    totalForms.setAttribute('value', `${aliasForm.length}`)
    btnDelete.forEach(addCallback)
}
