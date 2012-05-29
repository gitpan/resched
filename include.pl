#!/usr/bin/perl
# -*- cperl -*-

use strict;
require "./db.pl";
package include;
require "./sitecode.pl"; # Site-specific code should be moved into there.
use Carp;

my $ajaxscript = qq[<script language="javascript" src="ajax.js" type="text/javascript">\n</script>\n];

our %sidebarpos = ( right => 1 ) unless defined %sidebarpos; # Used by contentwithsidebar
# any of 'left', 'right', 'top', and 'bottom' that are set to true
# cause sidebar to appear there.  'right' only is the default.

sub datewithtwelvehourtime {
  my ($dt) = @_;
  confess "datewithtwelvehourtime() needs a DateTime object" if not ref $dt;
  return $dt->year() . '-' . $dt->month_abbr() . '-' . $dt->mday()
    . " at " . twelvehourtime($dt->hour() . ":" . sprintf "%02d", $dt->minute());
}

sub twelvehourtimefromdt {
  my ($dt) = @_;
  confess "twelvehourtimefromdt() needs a DateTime object" if not ref $dt;
  my $h = $dt->hour;
  my $m = sprintf "%02d", $dt->minute;
  $m = '' if ($m == 0 and $h ne 12);
  if ($h > 12) {
    $m .= "pm";
    $h -= 12;
  } elsif ($h < 12) {
    $m .= "am";
  }
  return $h . $m if $m =~ /^[ap]m$/;
  return $h . ":" . $m;
}

sub twelvehourtime {
  my ($time) = @_;
  my ($h, $m, $rest) = $time =~ /(\d+)[:](\d+)(.*)/;
  $rest = '0' . $rest if $rest =~ /^\d$/;
  if ($h > 12) {
    $h -= 12; $rest .= " pm";
  } else {
    $rest .= " am" unless $h == 12;
  }
  return $h . ":" . $m . $rest;
}


sub ordinalsuffix {
  my ($n) = @_;
  return "th" if ($n > 10 and $n < 14);
  my %th = ( 1 => 'st', 2 => 'nd', 3 => 'rd', map { ($_ => 'th') } (0, 4..9));
  return $th{($n =~ /.*(\d)/)[0]};
}

sub hasaliases {
  my ($name) = @_;
  my @result = main::findrecord('resched_alias', 'canon', $name);
  return @result;
}

sub isalias {
  my ($name) = @_;
  my @result = main::findrecord('resched_alias', 'alias', $name);
  if (@result) {
    return ${$result[-1]}{canon};
  } else {
    return; # false
  }
}

sub dealias {
  my ($name) = @_;
  my @result = main::findrecord('resched_alias', 'alias', $name);
  if (@result) {
    return ${$result[-1]}{canon};
  } else {
    return $name;
  }
}

sub normalisebookedfor {
  my ($rawname) = @_;
  my $normalname = lc $rawname;
  if ($normalname =~ /(.+)[,]\s*(.+)/) { $normalname = "$2 $1"; }
  $normalname = sitecode::normalisebookedfor($normalname);
  $normalname =~ s/\s+/ /g;
  $normalname =~ s/[.]//g;
  return $normalname;
}

sub capitalise {
  my ($name) = @_; # This should already be dealiased, if that is desired, and normalised.
  my @p = split /\s+/, $name;
  my @part;
  while (@p) {
    my $n = shift @p;
    $n = ucfirst lc $n;
    if ((scalar @part) > (scalar @p)) {
      # Given names ordinarily don't follow these patterns, but
      # surnames and suffices do:
      $n =~ s/^(Ma?c|Van|(?:[A-Z])(?:[']|[&]#39;))(\w)/$1 . ucfirst $2/e;
      $n =~ s/\b(ii|iii|iv|vi|vii|viii)\b/uc $1/ei;
    }
    push @part, $n;
  }
  return join " ", @part;
}

sub standardoutput {
  # This returns the complete http headers and the html
  # calling code must define sub main::usersidebar that
  # returns an appropriate div.
  my ($title, $content, $ab, $style, $meta, $favicon) = @_;
  my $cws = contentwithsidebar($content, "$ab\n".main::usersidebar());
  my $css = include::style($style);
  $favicon ||= 'resched.ico';
  return qq[Content-type: $include::content_type\n$auth::cookie

$include::doctype
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
   <!-- This page is served by resched, the Resource Scheduling tool. -->
   <!-- Created by Nathan Eady for Galion Public Library.  -->
   <!-- resched version 0.8.2 vintage 2012 May 29. -->
   <!-- See http://cgi.galion.lib.oh.us/staff/resched-public/ -->
   <title>$title</title>
   <link rel="SHORTCUT ICON" href="$favicon" />
   $ajaxscript
   $meta
   $css
</head>
<body>
  $cws
$include::footer
</body>
</html>];
}

sub sidebarstylesection {
  my ($preserve, $program) = @_;
  if ($preserve and not $preserve =~ /&amp;$/) {
    $preserve .= '&amp;';
  }
  $program ||= './';
  my $keepajax = qq[useajax=$main::input{useajax}];
  return qq[<div><strong><span onclick="toggledisplay('visualstylelist','visualstylemark');" id="visualstylemark" class="expmark">+</span>
        <span onclick="toggledisplay('visualstylelist','visualstylemark','expand');">Visual Style:</span></strong>
        <div id="visualstylelist" style="display: none;"><ul>
        <!-- Schemes with general appeal: -->
           <li><a href="${program}?${preserve}usestyle=lightondark&amp;$keepajax">Light on Dark</a></li>
           <li><a href="${program}?${preserve}usestyle=darkonlight&amp;$keepajax">Dark on Light</a></li>
           <li><a href="${program}?${preserve}usestyle=lowcontrast&amp;$keepajax">Low Contrast</a></li>
           <li><a href="${program}?${preserve}usestyle=browserdefs&amp;$keepajax">Browser Colors</a></li>
           <li><a href="${program}?${preserve}usestyle=funwithfont&amp;$keepajax">Fun with Fonts</a></li>
           <li><a href="${program}?${preserve}usestyle=blackonwite&amp;$keepajax">Black on White</a></li>
        </ul></div></div>];
}

sub contentwithsidebar {
  # It is up to the calling code to ensure $sidebar will display
  # properly in the position in question.  (This is especially an
  # issue for top or bottom 'sidebars'.
  my ($content, $sidebar) = @_;
  my $colspan = 1 + ($sidebarpos{left}?1:0) + ($sidebarpos{right}?1:0);
  return qq[<table border="0" class="contentwithsidebar" width="100%">]
    . ($sidebarpos{top} ?  qq[<tr class="sidebar"><td class="sidebar" colspan="$colspan">$sidebar</td></tr>]:"")
    . "<tr>" . ($sidebarpos{left} ? qq[<td class="sidebar">$sidebar</td>]:"")
             . qq[<td class="content">$content</td>]
             . ($sidebarpos{right} ? qq[<td class="sidebar">$sidebar</td>]:"")
             ."</tr>"
    . ($sidebarpos{bottom} ? qq[<tr class="sidebar"><td class="sidebar" colspan="$colspan">$sidebar</td></tr>]:"")
    . "</table>";
}



sub optionlist {
  my ($listname, $hashref, $default, $id) = @_;
  my %option = %{$hashref};
  $id ||= $listname;
  #use Data::Dumper; warn Dumper(@_);
  my $list = qq[<select name="$listname" id="$id">];
  for my $opt (sort { $a <=> $b } keys %option) {
    $list .= qq[<option value="$opt"].(($opt eq $default)?' selected="selected"':'').qq[>$option{$opt}</option>];
  }
  $list .= "</select>";
  #warn $list;
  return $list;
}

sub houroptions {
  my ($selectedhour) = @_;
  return join "\n            ",
    map {
      my $val = $_;
      my $hour = ($val <= 12) ? ("$val"."am") : (($val-12)."pm");
      my $selected = ($_ == $selectedhour) ? ' selected="selected"' : '';
      "<option value=\"$val\"$selected>$hour</option>"
    } 8..20;
}

our $doctype = "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">";
our $content_type = "text/html";

sub include::check_for_collision_using_datetimes {
  my ($res, $begdt, $enddt) = @_;
  die "check_for_collision_using_datetimes takes datetime arguments for the timeslot beginning and end" unless (ref $begdt and ref $enddt);
  my $beg = DateTime::Format::ForDB($begdt);
  my $end = DateTime::Format::ForDB($enddt);
  return include::check_for_collision($res, $beg, $end);
}
sub include::check_for_collision {
  # This is an optimization.  Previously we fetched all results for
  # the resource in question, made DateTime objects for their start
  # and end, and checked for overlap using DateTime::Duration.  That
  # was reliable, but this way is a big performance improvement.
  my ($res, $beg, $end) = @_;
  die "check_for_collision does not take datetime arguments; use check_for_collision_using_datetimes if you need that" if (ref $beg or ref $end);
  my $db = main::dbconn();
  my ($resid) = $res =~ /(\d+)/;
  my $q = $db->prepare("SELECT * FROM resched_bookings WHERE resource=? AND until > ? AND fromtime < ?");
  $q->execute($resid, $beg, $end);
  my (@answer, $r);
  while ($r = $q->fetchrow_hashref()) { push @answer, $r; }
  #warn "Checked for collisions on resource $res from $beg until $end: found " . scalar @answer . " collision(s) on behalf of $ENV{REMOTE_ADDR}.\n"; # TODO:  Comment this out when we're sure all is well.
  return @answer;
}

sub include::style {
  my ($s) = @_;
  $s ||= 'lowcontrast';
  my %stylesub = ( # a holdover from the old style system, for backward compatibility only.
                  manilla     => 'darkonlight',
                  hicmanilla  => 'darkonlight',
                  lightpurple => 'darkonlight',
                  softpurple  => 'lightondark',
                  burgundy    => 'lightondark',
                  neonlites   => 'lightondark',
                  britewite   => 'blackonwite',
                  jonadabian  => 'lightondark',
                 );
  $s = $stylesub{$s} if $stylesub{$s};
  my %style = (
               lightondark => qq[<link rel="stylesheet" type="text/css" media="screen" href="lightondark.css" title="Light on Dark Colors" />],
               darkonlight => qq[<link rel="stylesheet" type="text/css" media="screen" href="darkonlight.css" title="Dark on Light Colors" />],
               lowcontrast => qq[<link rel="stylesheet" type="text/css" media="screen" href="lowcontrast.css" title="Low Contrast" />],
               browserdefs => qq[<link rel="stylesheet" type="text/css" media="screen" href="browserdefs.css" title="Browser Colors" />],
               funwithfont => qq[<link rel="stylesheet" type="text/css" media="screen" href="funwithfont.css" title="Fun with Fonts" />],
               blackonwite => qq[<link rel="stylesheet" type="text/css" media="screen" href="blackonwite.css" title="Black on White" />],
              );
  my $style = join "\n", (map {
    $style{$_}
  } sort {
    ($a eq $s) ? -1 : (($b eq $s) ? 1 : ($b cmp $a))
  } keys %style), ($s ? $style{$s} : '');
  my $nonajaxstyle = qq[
<style type="text/css">

.nonajax {
  display: none;
}

.nobr {
  white-space: nowrap;
}

</style>] unless $main::input{ajax} eq 'off';
  return qq[
$style
<link rel="stylesheet" type="text/css" media="print"  href="print.css" />

$nonajaxstyle
];
}

our $footer = qq[<div class="footer">
<p class="noprint">Powered By <abbr title="Linux, Apache, MySQL, Perl"><a href="http://www.onlamp.com">LAMP</a></abbr>
   and <abbr title="Asynchronous Javascript And XML"><a href="http://en.wikipedia.org/wiki/AJAX">AJAX</a></abbr> Technologies:
<a href="http://www.linux.org"><img src="tux-small.png" alt="Linux, "></img></a>
<a href="http://www.apache.org"><img src="feather-small.png" alt="Apache, "></img></a>
<a href="http://www.mysql.com/"><img src="dolphin-blue-white-small.png" alt="MySQL, " width="36" height="32"></img></a>
<a href="http://www.perl.com/"><img src="camel-small.png" alt="Perl, " width="28" height="31"></img></a>
<a href="http://en.wikipedia.org/wiki/Javascript"><img src="rhino.png" alt="Javascript, " width="23" height="32" /></a>
<abbr title="Extensible Markup Language"><a href="http://www.w3.org/XML/"><code>&lt;xml/&gt;</code></a></abbr>
</p></div>\n];

our $localtimezone = main::getvariable('resched', 'time_zone') || "America/New_York";

sub categories {
  my $categories = main::getvariable('resched', 'categories');
  my @category;
  if ($categories) {
    @category = map {
      my ($catname, @id) = split /,\s*/, $_;
      [$catname, map { /(\d+)/; $1 } @id]
    } grep { $_ } split /\r?\n/, $categories;
  } else {
    @category = map {
      [$$_{name} => $$_{id}]
    } grep {
      not $$_{flags} =~ /X/
    } main::getrecord('resched_resources');
  }
  #use Data::Dumper; warn Dumper(+{ categories => \@category,
  #                                 variable   => $categories,
  #                               });
  return @category;
}

sub sgorpl {
  my ($num, $sg, $pl) = @_;
  if ($num == 1) {
    return(qq[$num $sg]);
  }
  return($num . ' ' . ($pl || ($sg . "s")));
}
sub isare {
  my ($num) = @_;
  return inflectverbfornumber($num, 'is', 'are');
}
sub inflectverbfornumber {
  my ($num, $sg, $pl) = @_;
  if (not defined $pl) {
    # Handles weak verbs only.
    if ($sg =~ /e$/) { $pl = $sg . 'd'; } else { $pl = $sg . 'ed'; }
  }
  return $sg if ($num == 1);
  return $pl;
}

sub parsemonth {
  local ($_)=@_;
  if    (/\d+/)   { return $1; }
  elsif (/^jan/i) { return  1; }
  elsif (/^feb/i) { return  2; }
  elsif (/^mar/i) { return  3; }
  elsif (/^apr/i) { return  4; }
  elsif (/^may/i) { return  5; }
  elsif (/^jun/i) { return  6; }
  elsif (/^jul/i) { return  7; }
  elsif (/^aug/i) { return  8; }
  elsif (/^sep/i) { return  9; }
  elsif (/^oct/i) { return 10; }
  elsif (/^nov/i) { return 11; }
  elsif (/^dec/i) { return 12; }
  else {
    return 0;
  }
}

1;
