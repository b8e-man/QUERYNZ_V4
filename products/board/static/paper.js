// The paper tab: a story whose picture cannot be had is set as type (its site's name on a plain block).
(function () {
  function none(img) { var p = img.parentNode; if (p) { p.classList.add("none"); p.removeChild(img); } }
  document.querySelectorAll(".pp-story .pic img").forEach(function (img) {
    if (img.complete && img.naturalWidth === 0 && img.getAttribute("src")) { none(img); }
    img.addEventListener("error", function () { none(img); });
  });
})();
