#!/usr/bin/perl -wT
# -*- cperl -*-

package DateTimeExtensions;
$ENV{PATH}='';
use DateTime::Format::MySQL;

sub DateTime::Format::ForDB {
  my ($dt) = @_;
  return DateTime::Format::MySQL->format_datetime($dt) if $dt;
  use Carp;
  carp "Vogon Folk Music: $dt, $@$!";
}

sub DateTime::From::MySQL {
  my ($dtstring, $tzone) = @_;
  $tzone ||= 'America/New_York';
  if ($dtstring =~ /(\d{4})-(\d{2})-(\d{2})\s+(\d{2})[:](\d{2})[:](\d{2})/) {
    return DateTime->new(
                         year   => $1,
                         month  => $2,
                         day    => $3,
                         hour   => $4,
                         minute => $5,
                         second => $6,
                         time_zone => $tzone,
                        );
  } else {
    warn "from_mysql cannot parse datetime string: '$dtstring'";
    return undef;
  }
  # It may be possible to simplify this using Time::Piece::MySQL,
  # which has a from_mysql_datetime method that returns the time
  # in the same format as time(), which can probably be fed to
  # DateTime::from_epoch
}

sub DateTime::Format::Cookie {
  my ($dt) = @_;
  $dt->set_time_zone('UTC');
  # Example of the correct format:  Wed, 01 Jan 3000 00:00:00 GMT
  return ((ucfirst $dt->day_abbr())   . ", " .
          sprintf("%02d",$dt->mday()) . " "  .
          $dt->month_abbr()           . " "  .
          sprintf("%04d", $dt->year)  . " "  .
          $dt->hms()                  . " GMT");
}


42;
