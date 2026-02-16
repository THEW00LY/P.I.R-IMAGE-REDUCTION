function setup() {
    document.getElementById('buttonid').addEventListener('click', openDialog);
    function openDialog() {
        document.getElementById('fileid').click();
    }
    document.getElementById('fileid').addEventListener('change', submitForm);
    function submitForm() {
        document.getElementById('formid').submit();
    }
}