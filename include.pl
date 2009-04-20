#!/usr/bin/perl
# -*- cperl -*-

use strict;
require "./db.pl";
package include;
require "./sitecode.pl"; # Site-specific code should be moved into there.

my $ajaxscript = qq[<script language="javascript" src="ajax.js" type="text/javascript">\n</script>\n];

our %sidebarpos = ( right => 1 ) unless defined %sidebarpos; # Used by contentwithsidebar
# any of 'left', 'right', 'top', and 'bottom' that are set to true
# cause sidebar to appear there.  'right' only is the default.

sub datewithtwelvehourtime {
  my ($dt) = @_;
  return $dt->ymd() . " at " . twelvehourtime($dt->hour() . ":" . sprintf "%02d", $dt->minute());
}

sub twelvehourtimefromdt {
  my ($dt) = @_;
  my $h = $dt->hour;
  my $m = sprintf "%02d", $dt->minute;
  $m = '' if ($m == 0 and $h ne 12);
  if ($h > 12) {
    $m .= "pm";
    $h -= 12;
  } elsif ($h < 12) {
    $m .= "am";
  }
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
  my @part = split /\s+/, $name;
  return join ' ', map {
    my $n = ucfirst lc $_;
    $n =~ s/^(Ma?c|Van)(\w)/$1 . ucfirst $2/e;
    $n =~ s/\b(ii|iii|iv|vi|vii|viii)\b/uc $1/ei;
    $n
  } @part;
}

sub standardoutput {
  # This returns the complete http headers and the html
  # calling code must define sub main::usersidebar that
  # returns an appropriate div.
  my ($title, $content, $ab, $style, $meta) = @_;
  my $cws = contentwithsidebar($content, "$ab\n".main::usersidebar());
  my $css = include::style($style);
  return qq[Content-type: $include::content_type\n$auth::cookie

$include::doctype
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
   <!-- This page is served by resched, the Resource Scheduling tool. -->
   <!-- Created by Nathan Eady for Galion Public Library.  -->
   <!-- resched version 0.7.7 vintage 2009 April 20. -->
   <!-- See http://cgi.galion.lib.oh.us/staff/resched-public/ -->
   <title>$title</title>
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

sub contentwithsidebar {
  # It is up to the calling code to ensure $sidebar will display
  # properly in the position in question.  (This is especially an
  # issue for top or bottom 'sidebars'.
  my ($content, $sidebar) = @_;
  my $colspan = 1 + ($sidebarpos{left}?1:0) + ($sidebarpos{right}?1:0);
  return "<table border=\"0\" class=\"contentwithsidebar\" width=\"100%\">"
    . ($sidebarpos{top}?   "<tr class=\"sidebar\"><td class=\"sidebar\" colspan=\"$colspan\">$sidebar</td></tr>":"")
    . "<tr>" . ($sidebarpos{left} ?"<td class=\"sidebar\">$sidebar</td>":"")
             . "<td class=\"content\">$content</td>"
             . ($sidebarpos{right}?"<td class=\"sidebar\">$sidebar</td>":"")
             ."</tr>"
    . ($sidebarpos{bottom}?"<tr class=\"sidebar\"><td class=\"sidebar\" colspan=\"$colspan\">$sidebar</td></tr>":"")
    . "</table>";
}

sub optionlist {
  my ($listname, $hashref, $default) = @_;
  my %option = %{$hashref};
  my $list = "<select name=\"$listname\">";
  for (sort { $a <=> $b } keys %option) {
    $list .= "<option value=\"$_\"".(($_ eq $default)?" selected=\"selected\"":"").">$option{$_}</option>";
  }
  $list .= "</select>";
  return $list;
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
  return 'is' if ($num == 1);
  return 'are';
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
