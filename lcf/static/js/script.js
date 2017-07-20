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

function toggleIcon(glyph) {
    if (glyph.hasClass("glyphicon-chevron-down")) {
      glyph.removeClass("glyphicon-chevron-down").addClass("glyphicon-chevron-up");
    }
    else if (glyph.hasClass("glyphicon-chevron-up")) {
      glyph.removeClass("glyphicon-chevron-up").addClass("glyphicon-chevron-down");
    }
}

$(document).ready(function(){
    //$( "div.btn-primary" ).click(function(){$(this).html("changed");});
    //var button = document.getElementsByClassName('btn-primary')[0]
    //button.onclick = function(){button.innerHTML = "changed"}

    //$(".edit-button").click(function(){
    //  toggleEditable();
    //});


    $(".hide-button0").click(function(){
      $(".to-hide0").slideToggle();
      toggleIcon($(this));
    });

    $(".hide-button1").click(function(){
      $(".to-hide1").slideToggle();
      toggleIcon($(this));
    });

    $(".hide-button2").click(function(){
      $(".to-hide2").slideToggle();
      toggleIcon($(this));
    });

    $(".hide-button3").click(function(){
      $(".to-hide3").slideToggle();
      toggleIcon($(this));
    });

    $(".hide-button4").click(function(){
      $(".to-hide4").slideToggle();
      toggleIcon($(this));
    });

    $(".hide-button5").click(function(){
      $(".to-hide5").slideToggle();
      toggleIcon($(this));
    });

    $(".hide-button6").click(function(){
      $(".to-hide6").slideToggle();
      toggleIcon($(this));
    });

    $(".hide-button7").click(function(){
      $(".to-hide7").slideToggle();
      toggleIcon($(this));
    });


    $(".hide-button8").click(function(){
      $(".to-hide8").slideToggle();
      toggleIcon($(this));
    });

    $(".confirm-delete").click(function(){
        return confirm('Are you sure you want to delete this?');
    })


//    document.getElementById("id_all_excel_quirks").onclick = function(){toggle(this)}
    $('th:contains("Subtotal")').addClass('sub');
    $('th:contains("Innovation premium (ignores negawatts)")').addClass('sub');
    $('th:contains("Total")').addClass('tot');

});
