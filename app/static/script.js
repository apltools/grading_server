var id = "";

document.addEventListener("DOMContentLoaded", function(event) {
  $("#check50_form").submit(function(e) {
    e.preventDefault();
    var formData = new FormData(this);

    for (var [key, value] of formData.entries()) {
      console.log(key, value);
    }

    $.ajax({
        url: "/check50",
        type: 'POST',
        data: formData,
        success: function(data) {
            id = data.id;
            console.log(id, data);
            $("#post_result").val(JSON.stringify(data, null, 2));
        },
        error: function(data) {
            $("#post_result").val(data.responseText);
        },
        cache: false,
        contentType: false,
        processData: false
    });
  });

  $("#checkpy_form").submit(function(e) {
    e.preventDefault();
    var formData = new FormData(this);

    for (var [key, value] of formData.entries()) {
      console.log(key, value);
    }

    $.ajax({
        url: "/checkpy",
        type: 'POST',
        data: formData,
        success: function(data) {
            id = data.id;
            console.log(id, data);
            $("#post_result").val(JSON.stringify(data, null, 2));
        },
        error: function(data) {
            $("#post_result").val(data.responseText);
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
              $("#result").val(JSON.stringify(data, null, 2));
            }
            else if (data["status"] == "failed") {
              id = "";
              console.log(data["result"]);
              $("#result").val(data);
            }
            else {
              $("#result").val(JSON.stringify(data, null, 2));
            }
          }
      });
    }
  }, 1000);
});
