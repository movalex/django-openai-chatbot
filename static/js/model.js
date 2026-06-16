const select = document.getElementById('floatingSelect');
const modelField = document.getElementById('modelIdField');
modelField.value = select.dataset.defaultModel;
select.addEventListener('change', function (){
    modelField.value = this.value;
})
