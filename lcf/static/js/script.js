function toggleText() {
  if (document.getElementById("myText").disabled == false) {
      document.getElementById("myText").disabled = true;
    }
    else {
      document.getElementById("myText").disabled = false;
    }

}





$(document).ready(function(){
    //$( "div.btn-primary" ).click(function(){$(this).html("changed");});
    //var button = document.getElementsByClassName('btn-primary')[0]
    //button.onclick = function(){button.innerHTML = "changed"}
    $(".hide-button").click(function(){
      $(".to-hide").slideToggle();
    });
});
