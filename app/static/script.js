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
        success: function(data) {
            id = data.id;
            console.log(id, data);
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
          success: function(data) {
            console.log("polling", data);
            if (data["status"] == "finished") {
              id = "";
              console.log(data["result"]);
              $("#result").text(JSON.stringify(data["result"]), null, 2);
            }
            else if (data["status"] == "failed") {
              id = "";
              console.log(data["result"]);
              $("#result").text(data["result"]);
            }
          }
      });
    }
  }, 1000);
});
