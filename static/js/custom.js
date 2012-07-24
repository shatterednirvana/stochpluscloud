$(document).ready(function() {

  $('#cloud').click(function() {
    runStochKit('cloud');
  });

  $('#local').click(function() {
    runStochKit('local');
  });


}); // end document/ready


function runStochKit(whereToRun) {
  // TODO(cgb): validate these params first, and if they're good...

  // require params
  // TODO(cgb): model
  var time = $('#time').val();
  var realizations = $('#realizations').val();

  // optional params
  var keep_trajectories = get_checked_for('#keep-trajectories');
  var keep_histograms = get_checked_for('#keep-histograms');
  var label = get_checked_for('#label');
  var seed = $('#seed').val();
  var epsilon = $('#epsilon').val();
  var threshold = $('#threshold').val();

  // TODO(cgb): whereToRun

  /*
  $.ajax({
    type: 'POST',
    async: true,
    url: '/run',
    data: {
            
    },
    success: function(data) {
      components = JSON.parse(data);  // gives us [{name. ip}]
  }

  }); */
}


function get_checked_for(id) {
  if ($(id).is(':checked')) {
    return true;
  } else {
    return false;
  }
}
