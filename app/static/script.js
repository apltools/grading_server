var id = "";

function post(form, dest) {
  form.submit(function(e) {
    e.preventDefault();
    var formData = new FormData(this);

    for (var [key, value] of formData.entries()) {
      console.log(key, value);
    }

    $.ajax({
        url: dest,
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
}

document.addEventListener("DOMContentLoaded", function(event) {
  post($("#check50_form"), "/check50");
  post($("#check50v2_form"), "/check50v2");
  post($("#checkpy_form"), "/checkpy");

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
              $("#result").val(JSON.stringify(data, null, 2));
            }
            else {
              $("#result").val(JSON.stringify(data, null, 2));
            }
          }
      });
    }
  }, 1000);
});
