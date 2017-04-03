//function toggleEditable() {
//    if ( element.prop('disabled', true)) {
//        element.prop('disabled', false);
//    }
//    else {
//        element.prop('disabled', true);
//    };

//  if (document.getElementsByTagName("input").disabled == false) {
//      document.getElementsByTagName("input").disabled = true;
//    }
//    else {
//      document.getElementsByTagName("input").disabled = false;
//    }

//}




function toggle(source) {
  var checkboxes = [document.getElementById('id_excel_2020_gen_error'),
                    document.getElementById('id_excel_nw_carry_error'),
                    document.getElementById('id_excel_sp_error')]
  for(var i=0, n=checkboxes.length;i<n;i++) {
    checkboxes[i].checked = source.checked;
  }
}


$(document).ready(function(){
    //$( "div.btn-primary" ).click(function(){$(this).html("changed");});
    //var button = document.getElementsByClassName('btn-primary')[0]
    //button.onclick = function(){button.innerHTML = "changed"}

    //$(".edit-button").click(function(){
    //  toggleEditable();
    //});


    $(".hide-button").click(function(){
      $(".to-hide").slideToggle();
    });


//    document.getElementById("id_all_excel_quirks").onclick = function(){toggle(this)}

});
