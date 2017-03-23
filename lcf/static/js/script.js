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



});
