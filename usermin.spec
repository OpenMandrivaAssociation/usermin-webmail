%define __spec_install_post %{nil}

Summary:	A web-based user account administration interface
Name:		usermin
Version:	1.440
Release:	%mkrel 1
Provides:	%{name}-%{version}
License:	BSD
Group:		System/Configuration/Other
URL:		http://www.usermin.com/
Source:		http://www.webmin.com/download/%{name}-%{version}.tar.gz
Patch3:		usermin-1.440-never-fail-detect-os.patch
Requires:	perl
Requires(pre):	rpm-helper
Requires:	perl perl-Net_SSLeay 
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch:	noarch

%description
A web-based user account administration interface for Unix systems.

After installation, enter the URL https://localhost:20000/ into your
browser and login as any user on your system.

%prep
%setup -q
%patch3 -p0

perl -pi -e 's|/tmp/.webmin|/root/.webmin|' *

%build
(find . -name '*.cgi' ; find . -name '*.pl') | perl perlpath.pl %{_bindir}/perl -
rm -f mount/freebsd-mounts-*
rm -f mount/openbsd-mounts-*
#chmod -R og-rxw .

%install
mkdir -p %{buildroot}{%{_sysconfdir}/{pam.d,sysconfig},%{_initrddir},%{_var}/run/usermin,%{_datadir}/usermin}

cp -rp * %{buildroot}%{_datadir}/usermin

cp usermin-daemon %{buildroot}%{_sysconfdir}/sysconfig/usermin
cp usermin-init %{buildroot}%{_initrddir}/usermin
cp usermin-pam %{buildroot}%{_sysconfdir}/pam.d/usermin

# Fix perms for rpmlint:
find %{buildroot}%{_datadir}/usermin ! -type d -exec chmod 644 {} \;

find %{buildroot}%{_datadir}/usermin \( \
	-type d \
	-o -name "*.sh" -o -name "*.cgi" \
	-o -name "install-module.pl" -o -name "web-lib.pl" \
	-o -name "miniserv.pl" -o -name "newmods.pl" \
	-o -name "cron_editor.pl" -o -name "autoreply.pl" \
	-o -name "theme.pl" -o -name "solaris-lib.pl" \
	-o -name "unixware-lib.pl" \
	-o -name "msctile2.jpg" -o -name "theme_by.jpg" \
	-o -name "webmin_logo.jpg" \
	\) \
	-exec chmod 755 {} \;

echo rpm >%{buildroot}%{_datadir}/usermin/install-type

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%pre
perl <<EOD;
# maketemp.pl
# Create the /root/.webmin directory if needed
# ASkwar:
# This really needs to be /root/.webmin, because of (at least) the setup.sh
# script

\$tmp_dir = "/root/.webmin";

if (!-d \$tmp_dir) {
	mkdir(\$tmp_dir, 0755) || exit 1;
	chown(\$<, \$(, \$tmp_dir);
	chmod(0755, \$tmp_dir);
	}
@st = stat(\$tmp_dir);
if (@st && \$st[4] == \$< && \$st[5] == \$( && \$st[2] & 0x4000 &&
    (\$st[2] & 0777) == 0755) {
	exit 0;
	}
else {
	exit 1;
	}


EOD
if [ "$?" != "0" ]; then
	echo "Failed to create or check temp files directory /root/.webmin"
	exit 1
fi

%post
if [ "$1" != 1 ]; then
	# Upgrading the RPM, so stop the old usermin properly
	service usermin stop
fi
cd %{_datadir}/usermin
config_dir=%{_sysconfdir}/usermin
var_dir=%{_var}/run/usermin
perl=%{_bindir}/perl
autoos=1
port=20000
host=`hostname`
ssl=1
atboot=1
nochown=1
autothird=1
noperlpath=1
nouninstall=1
nostart=1
export config_dir var_dir perl autoos port host ssl nochown autothird noperlpath nouninstall nostart allow
./setup.sh > /root/tmp/usermin-setup.out 2>/root/tmp/usermin-setup.err

cat > %{_sysconfdir}/usermin/uninstall.sh <<EOFF
#!/bin/sh
printf "Are you sure you want to uninstall Usermin? (y/n) : "
read answer
printf "\n"
if [ "\$answer" = "y" ]; then
	echo "Removing usermin RPM .."
	#rpm -e --nodeps usermin
	urpme usermin
	echo "Done!"
fi
EOFF
chmod +x %{_sysconfdir}/usermin/uninstall.sh

%_post_service usermin

%preun
%_preun_service usermin

%postun
if [ "$1" = 0 ]; then
	grep root=%{_datadir}/usermin %{_sysconfdir}/usermin/miniserv.conf >/dev/null 2>&1
	if [ "$?" = 0 ]; then
		# RPM is being removed, and no new version of usermin
		# has taken it's place. Delete the config files
		rm -rf %{_sysconfdir}/usermin %{_var}/usermin
	fi
fi

%files
%defattr(-,root,root)
%doc LICENCE* README
#%{_libexecdir}/usermin
%{_datadir}/usermin
%config(noreplace) %{_sysconfdir}/sysconfig/usermin
%config(noreplace) %{_sysconfdir}/pam.d/usermin
%config(noreplace) %{_initrddir}/usermin

