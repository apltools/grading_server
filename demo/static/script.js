var id = "";

document.addEventListener("DOMContentLoaded", function(event) {
  $("#form").submit(function(e) {
    e.preventDefault();
    var formData = new FormData(this);

    for (var [key, value] of formData.entries()) {
      console.log(key, value);
    }

    $.ajax({
        url: "/start",
        type: 'POST',
        data: formData,
        success: function (data) {
            id = data;
            console.log(id);
        },
        cache: false,
        contentType: false,
        processData: false
    });
  });

  window.setInterval(function() {
    if (id !== "") {
      $.ajax({
          url: "/get/" + id,
          type: 'GET',
          dataType: 'json',
          success: function (data) {
            console.log("polling");
            if (data["message"] == "finished") {
              id = "";
              console.log(data["result"]);
              $("#result").text(JSON.stringify(data["result"]), null, 2);
            }
          }
      });
    }
  }, 1000);
});

function send(slug) {
  $.ajax({
    url:"/get/nope",
    success:function(json){
      console.log(json);
    },
    error:function(){
      alert("Error");
    }
  });
}