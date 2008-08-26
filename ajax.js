var request = false;
var baseuri = 'http://cgi.galion.lib.oh.us/staff/resched-public/resched/dynamic-info.cgi';
try {
  request = new XMLHttpRequest();
} catch (trymicrosoft) {
  try {
    request = new ActiveXObject("Msxml2.XMLHTTP");
  } catch (othermicrosoft) {
    try {
      request = new ActiveXObject("Microsoft.XMLHTTP");
    } catch (failed) {
      request = false;
    }
  }
}
function handleResponse() {
  if (request.readyState==4) {
    var resultdom = request.responseXML.documentElement;
    var alerts = resultdom.getElementsByTagName("alert");
    if (alerts && alerts[0]) {
       var alerttext = alerts[0].firstChild.data;
       alert(alerttext);
    }
    var updc = resultdom.getElementsByTagName("updatecount");
    if (updc && updc[0]) {
       retrieveupdates();
    }
    var repl = resultdom.getElementsByTagName("replace");
    if (repl  && repl[0]) {
       var containerid = resultdom.getElementsByTagName("replace_within")[0].firstChild.data;
       var container   = document.getElementById(containerid);
       var newcontent  = resultdom.getElementsByTagName("replacement")[0].firstChild;
       var oldnode     = container.childNodes;
       var numnodes    = oldnode.length;
       for (var i=numnodes-1; i >= 0; i--) {
          container.removeChild(oldnode[i]);
       }
       container.appendChild(newcontent);
    }
    var foc = resultdom.getElementsByTagName("focus");
    if (foc && foc[0]) {
       var focid = foc[0].firstChild.data;
       var focel = document.getElementById(focid);
       focel.focus();
    }
}}

function sendajaxrequest(myargs) {
   var uri = baseuri + '?' + myargs;
   //alert(uri);
   request.open("GET", uri, true);
   request.onreadystatechange=handleResponse;
   request.send(null);
}
function onemoment(containerid) {
   var container = document.getElementById(containerid);
   insert_before_element('One Moment...', container.firstChild)
}
function toggledisplay(eltid, expansionmarker, coerce) {
  var elt = document.getElementById(eltid);
  if ((elt.style.display == "none") || (coerce=='expand')) {
    elt.style.display = "inline";
  } else {
    elt.style.display = "none";
  }
  if (expansionmarker) {
     var expansionelt = document.getElementById(expansionmarker);
     if (elt.style.display == "none") {
        expansionelt.firstChild.data = '+';
     } else {
        expansionelt.firstChild.data = '-';
     }
  }
}

  function insert_before_element(what, where) {
      // This function is black, cargo-cult magic of the worst kind.
      // But it works, at least in Gecko.  It comes from the Open Clip
      // Art Library's svg upload tool, which uses it to let clip-art
      // authors add an arbitrary number of keywords.  The OCAL got the
      // jist of it from http://developer.osdl.org/bryce/js_test/test_7.html
      var range = where.ownerDocument.createRange(); // I have no clue what this does,
      range.setStartBefore(where);                   // much less this, or why it's necessary.
      where.parentNode.insertBefore(range.createContextualFragment(what),where);
  }

function changerecurform() {
  var selectelt      = document.getElementById('recurformselect');
  var recurstyleselt = document.getElementById('recurstyles');
  var recurlistelt   = document.getElementById('recurlist');
  if (selectelt.value == 'listed') {
    recurstyleselt.style.display = "none";
    recurlistelt.style.display = "inline";
  } else {
    if (selectelt.value == '') {
      recurstyleselt.style.display = "none";
      recurlistelt.style.display = "none";
    } else {
      recurstyleselt.style.display = "inline";
      recurlistelt.style.display = "none";
    }
  }
}

var datenumber = 1;
function augmentdatelist(year) {
  datenumber = datenumber + 1;
  var newcontent = '<tr><td><input type="text" name="recurlistyear' + datenumber + '" size="5" value="' + year + '" /></td>'
                 +  '        <td><select name="recurlistmonth' + datenumber + '">'
                 +  '              <option value="1">Jan</option>  <option value="2">Feb</option>  <option value="3">Mar</option>'
                 +  '              <option value="4">Apr</option>  <option value="5">May</option>  <option value="6">Jun</option>'
                 +  '              <option value="7">Jul</option>  <option value="8">Aug</option>  <option value="9">Sep</option>'
                 +  '              <option value="10">Oct</option> <option value="11">Nov</option> <option value="12">Dec</option>'
                 +  '             </select></td>'
                 +  '        <td><input type="text" name="recurlistmday' + datenumber + '" size="3" /></td>';
  var elt = document.getElementById('insertmorelisteddateshere');
  insert_before_element(newcontent, elt);
}
