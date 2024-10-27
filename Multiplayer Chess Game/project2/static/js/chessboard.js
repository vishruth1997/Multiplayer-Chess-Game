function movePiece() {
    var src = document.getElementById('src').value.toLowerCase();
    var dst = document.getElementById('dst').value.toLowerCase();
  
    var srcCell = document.getElementById(src);
    var dstCell = document.getElementById(dst);
  
    if (srcCell && dstCell) {
        dstCell.innerHTML = srcCell.innerHTML;
        srcCell.innerHTML = '&nbsp;';
    }
  }
  
  function resetBoard() {
    window.location.reload();
  }
  