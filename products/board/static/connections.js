// The connections pane beside the report on the subject report tab (Arthur, 10 November 2026; ruling 159). A tick or a
// dropdown changed sends the pane's form at once: the report is rebuilt with the setting, because a setting changes
// what is followed, not only what is shown. The settings are in the address the form sends, so the report reopens as
// it was. Without this script the pane's own button sends the same form.
(function () {
  "use strict";
  var forms = document.querySelectorAll("form.connections");
  for (var i = 0; i < forms.length; i++) {
    (function (form) {
      var controls = form.querySelectorAll("select, input[type=checkbox]");
      for (var j = 0; j < controls.length; j++) {
        controls[j].addEventListener("change", function () { form.submit(); });
      }
    })(forms[i]);
  }
})();
