#!/usr/bin/perl -T
# -*- cperl -*-

$ENV{PATH}='';
$ENV{ENV}='';

require "./forminput.pl";
require "./include.pl";
require "./auth.pl";

our %input = %{getforminput()};
my $ab = authbox(sub { my $x = getrecord('users', shift); "<!-- Hello, $$x{nickname} -->"; });

my %cfgvar =
  (
   sysadmin_name => +{  default     => 'the system administrator',
                        description => 'Name of the person responsible for administration of this installation of resched.',
                        sortkey     => 1,
                     },
   url_base => +{ default => '/resched/',
                  description => 'URL path to the directory where resched is installed.  This should end with a slash.  It may be absolute (with protocol and fqdn) or may begin with slash.',
                  sortkey => 5,
                },
   time_zone => +{ default => 'America/New_York',
                   description => 'Timezone for your site.  Specify a time_zone designation recognizeable by <a href="http://search.cpan.org/search?query=DateTime&mode=all">DateTime</a>.',
                   sortkey => 9,
                 },
   ils_name => +{ default => 'the ILS',
                  description => 'The name of the Integrated Library System software your library uses.',
                  sortkey => 20,
                },
   categories => +{
                   default => '',
                   description => 'If you divide your resources into categories, list them here, one per line.  (Follow the name of each category by a comma, and the ID numbers of the resources in that category, also separated by commas.)  Links in the sidebar (e.g., under Today) will point to entire categories, showing the resources in that category side-by-side.  Also, the statistics will be grouped and subtotaled by category.  The default is for each resource to be its own category, which works well if you only have two or three resources.',
                   sortkey => 210, multiline => 1,
                  },
   sidebar_post_today => +{ default     => '',
                            description => 'Wellformed XHTML snippet to insert in the sidebar between the Today section and the Rooms (1 week) section.  Must be allowable inside a block-level element.',
                            multiline   => 1, sortkey => 220,
                          },
   nonusers => +{
                 default => 'closed,maintenance,out of order',
                 description => 'Comma-separated list of special names that resources can be booked for, which should not count toward usage statistics.',
                 sortkey => 310,
                },
  );

if ($auth::user) {
  my $notice = '';
  my $title = "resched configuration";
  if ($input{action} eq 'save') {
    ($notice, $title) = savechanges();
  }
  print include::standardoutput($title,
                                $notice . configform(),
                                $ab, $input{usestyle});
} else {
  print include::standardoutput('Authentication Needed',
                                "<p>In order to access this page you need to log in.</p>",
                                $ab, $input{usestyle});
}

sub savechanges {
  my $changecount;
  for my $var (keys %cfgvar) {
    my $oldvalue = getvariable('resched', $var);
    my $newvalue = $input{'cfgvar_'.$var};
    if ($newvalue ne $oldvalue) {
      setvariable('resched', $var, $newvalue) if $newvalue ne $oldvalue;
      ++$changecount;
    }
  }
  my $title = $changecount ? include::sgorpl($changecount, 'changes') . ' saved' : 'Nothing Changed';
  my $notice = $changecount
    ? qq[<div class="info">Saved changes to ] . include::sgorpl($changecount, 'variable') . qq[</div>]
    : qq[<div class="error">No changes were made!</div>];
  return ($notice, $title);
}

sub configform {
  for my $var (keys %cfgvar) {
    ${$cfgvar{$var}}{value} = getvariable('resched', $var) || ${$cfgvar{$var}}{default};
  }
  return qq[<form id="configform" action="config.cgi" method="POST">
    <input type="hidden" name="action" value="save" />
    <table class="configtable"><tbody>] . (join "\n", map {
      my $var = $_;
      my $value = encode_entities(${$cfgvar{$var}}{value});
      my $inputelt = ${$cfgvar{$var}}{multiline}
        ? qq[<textarea cols="40" rows="5" name="cfgvar_$var">$value</textarea>]
        : qq[<input size="40" name="cfgvar_$var" value="$value" />];
      qq[<tr class="cfgvar"><td>$var</td>
         <td>$inputelt</td>
         <td>${$cfgvar{$var}}{description}
             (Default: <q>${$cfgvar{$var}}{default}</q>)</td></tr>]
    } sort { ${$cfgvar{$a}}{sortkey} <=> ${$cfgvar{$b}}{sortkey} } keys %cfgvar) . qq[</tbody></table>
    <input type="submit" value="Save Changes" />
  </form>]
}

sub usersidebar {
  return '<div class="sidebar"><div><a href="index.cgi">Return to the index.</a></div></div>';
}
