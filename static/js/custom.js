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

  // required params
  var model = $("input[name=model_name]:checked", '#form').val()
  var time = $('#time').val();
  var realizations = $('#realizations').val();
  var output = $('#output').val();

  // optional params
  var keep_trajectories = get_checked_for('#keep-trajectories');
  var keep_histograms = get_checked_for('#keep-histograms');
  var label = get_checked_for('#label');
  var seed = $('#seed').val();
  var epsilon = $('#epsilon').val();
  var threshold = $('#threshold').val();

  // TODO(cgb): whereToRun

  var params = {
    'model':model,
    'time':time,
    'realizations':realizations,
    'output':output,
    'keep-trajectories':keep_trajectories,
    'keep-histograms':keep_histograms,
    'label':label,
    'seed':seed,
    'epsilon':epsilon,
    'threshold':threshold,
    'where_to_run':whereToRun
  }

  $.ajax({
    type: 'POST',
    async: true,
    url: '/run',
    data: {'parameters':JSON.stringify(params)},
    success: function(data) {
      var something = JSON.parse(data);
  }

  });
}


function get_checked_for(id) {
  if ($(id).is(':checked')) {
    return true;
  } else {
    return false;
  }
}
