package providers

import (
	"errors"
	"fmt"
	"io/ioutil"
	"net"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	models "github.com/UCCNetsoc/nsa3/websites/pkg/models"
)

// Websites represents a provider that gives information about websites it can provide in both valid, and invalid configurations
type Websites interface {
	List() ([]models.Website, []models.InvalidWebsite, error)
	ByUser(username string) ([]models.Website, []models.InvalidWebsite, error)
}

// UserHomeDirWebsites provides websites named after domains inside a folder in a users home directory
// e.g. /home/ocanty/www/ocanty.netsoc.co
type UserHomeDirWebsites struct {
	homeDirsRoot string   // The directory which contains individual user folders (usually "/home/"), we assume a users home dir name matches their name
	wwwDirName   string   // The directory inside a users home directory to look for websites (usually "www")
	domain       string   // The base domain used for user subdomains (i.e netsoc.co)
	aRecords     []string // A records that each of the vHosts of a website domains HAVE to point to
	txtSubdomain string   // The TXT subdomain that we will find the users username at, to verify they own their domain
}

// MakeUserHomeDirWebsites 
func MakeUserHomeDirWebsites(homeDirsRoot string, wwwDirName string, domain string, aRecords []string, txtSubdomain string) (*UserHomeDirWebsites, error) {
	absHomeDirsRoot, err := filepath.Abs(homeDirsRoot)
	if err != nil {
		return nil, fmt.Errorf("Could not get absolute path of %s: %w", homeDirsRoot, err)
	}

	return &UserHomeDirWebsites{
		homeDirsRoot: absHomeDirsRoot,
		wwwDirName:   wwwDirName,
		domain:       domain,
		aRecords:     aRecords,
		txtSubdomain: txtSubdomain,
	}, nil
}

var domainRe = regexp.MustCompile(`^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|([a-zA-Z0-9][a-zA-Z0-9-_]{1,61}[a-zA-Z0-9]))\.([a-zA-Z]{2,6}|[a-zA-Z0-9-]{2,30}\.[a-zA-Z]{2,3})$`)

// Validate a vHost
func (p *UserHomeDirWebsites) validateVHost(vHost string, user string) error {
	if !domainRe.MatchString(vHost) {
		// Tut tut
		return fmt.Errorf("Invalid domain name format")
	}

	// First we need to check if the domain has the correct A records set
	names, err := net.LookupHost(vHost)

	if err != nil {
		return fmt.Errorf("Could not perform DNS lookup: %s", err)
	}

	if len(names) == 0 {
		return errors.New("No A/AAAA records associated with domain")
	}

	// sort.Strings(names)
	// for i, v := range names {
	// 	if v != p.aRecords[i] {
	// 		return fmt.Errorf("Found an A/AAAA record (%s) that does not match %s", v, p.aRecords[i])
	// 	}
	// }

	// If the website uses a subdomain of the base domain
	// i.e user.netsoc.co
	if strings.HasSuffix(vHost, "."+p.domain) {
		domain := strings.Split(vHost, ".")
		if domain[0] == user {
			return nil
		}

		return errors.New("The subdomain in use must match the account's username")
	}

	domainS := strings.Split(vHost, ".")

	// If the website is a domain other than subdomain.netsoc.co
	// We need to DNS record it and check if they have the correct TXT records set
	txtDomain := fmt.Sprintf("%s.%s.%s", p.txtSubdomain, domainS[len(domainS)-2], domainS[len(domainS)-1])
	txts, err := net.LookupTXT(txtDomain)
	if err != nil {
		return fmt.Errorf("Could not perform DNS TXT record lookup on %s.%s: %w", p.txtSubdomain, vHost, err)
	}

	if len(txts) != 0 && txts[0] != user {
		return fmt.Errorf("Could not find a DNS TXT record for %s.%s containing '%s'", p.txtSubdomain, vHost, user)
	}

	return nil
}

// List websites
func (p *UserHomeDirWebsites) List() ([]models.Website, []models.InvalidWebsite, error) {
	// Try and read /home/<user>/www directory
	homeDirsRootFd, err := os.Open(p.homeDirsRoot)
	defer homeDirsRootFd.Close()
	if err != nil {
		return nil, nil, fmt.Errorf("%s is inaccesible: %w", p.homeDirsRoot, err)
	}

	homeDirs, err := homeDirsRootFd.Readdirnames(0)
	if err != nil {
		return nil, nil, fmt.Errorf("%s: could not ls: %w", p.homeDirsRoot, err)
	}

	valid := make([]models.Website, 0)
	invalid := make([]models.InvalidWebsite, 0)
	for _, homeDir := range homeDirs {
		userValid, userInvalid, err := p.ByUser(homeDir)

		if err != nil {
			// Ignore bad users
			continue
		}

		valid = append(valid, userValid...)
		invalid = append(invalid, userInvalid...)
	}

	return valid, invalid, nil
}

// ByUser returns a list of valid and invalid websites for a home directory/username
func (p *UserHomeDirWebsites) ByUser(homeDir string) ([]models.Website, []models.InvalidWebsite, error) {
	wwwDirPath := fmt.Sprintf("%s/%s/%s", p.homeDirsRoot, homeDir, p.wwwDirName)

	wwwDirStat, err := os.Stat(wwwDirPath)
	if err != nil {
		return nil, nil, fmt.Errorf("%s is inaccessible: %w", wwwDirPath, err)
	}

	if !wwwDirStat.IsDir() {
		return nil, nil, fmt.Errorf("www is not a directory")
	}

	// Try and read /home/<user>/www directory
	websiteDirs, err := ioutil.ReadDir(wwwDirPath)

	if err != nil {
		return nil, nil, fmt.Errorf("Could not get user website: %s", err)
	}

	// Indexed by the root path to the website
	websites := make(map[string]*models.Website)

	// Invalid websites, ones with an error
	invalid := make([]models.InvalidWebsite, 0)

	// We want to process all the non-symlinks first, so sort by dir
	sort.Slice(websiteDirs, func(i, j int) bool {
		return websiteDirs[i].IsDir()
	})

	for _, websiteDir := range websiteDirs {
		vHost := websiteDir.Name()
		fmt.Println(vHost)

		// Resolve any symlink
		root, err := filepath.EvalSymlinks(fmt.Sprintf("%s/%s", wwwDirPath, vHost))

		if err != nil {
			// If invalid symlink, it's an invalid website
			invalid = append(invalid, models.InvalidWebsite{
				Hosts: []string{vHost},
				Root:  "",
				Error: fmt.Errorf("Invalid website symlink: %w", err),
			})

			// Move to next website
			continue
		}

		// Do not remove this check or you will allow for directory traversal attacks.
		err = p.validateVHost(vHost, homeDir)

		if err != nil {
			invalid = append(invalid, models.InvalidWebsite{
				Hosts: []string{vHost},
				Root:  root,
				Error: fmt.Errorf("Invalid domain: %w", err),
			})

			continue
		}

		// If they're defining a directory website, i.e ...www/jim.netsoc.co
		if websiteDir.IsDir() {
			websites[root] = &models.Website{
				Hosts: []string{vHost},
				Root:  root,
			}
		} else if websiteDir.Mode()&os.ModeSymlink != 0 {
			// If they're using a symlink
			// We need to check if they're defining a symlink to either another directory website i.e ...www/thelifeofjim.com -> ...www/jim.netsoc.co
			// or if they're defining a symlink into the a directory of a directory website i.e ...www/blog.thelifeofjim.com -> ...www/jim.netsoc.co/wordpress

			// If the symlink points at an existing website directory
			if _, ok := websites[root]; ok {
				// Add the symlink domain name as a vhost to that website
				websites[root].Hosts = append(websites[root].Hosts, vHost)
				continue
			}

			// We now need to check if the symlink points at a directory inside a website directory

			// First stat the location it's pointing to
			dest, err := os.Stat(root)
			if err != nil {
				// If bad state, it's an invalid website
				invalid = append(invalid, models.InvalidWebsite{
					Hosts: []string{vHost},
					Root:  root,
					Error: fmt.Errorf("Could not lookup symlink target: %w", err),
				})

				// Move to next website
				continue
			}

			// If the target isn't a directory
			if !dest.IsDir() {

				// Can't point a website symlink at a non-directory
				invalid = append(invalid, models.InvalidWebsite{
					Hosts: []string{vHost},
					Root:  root,
					Error: fmt.Errorf("Symlink %s does not point to a website or directory", dest.Name()),
				})

				// Move to next website
				continue
			}

			rel, err := filepath.Rel(wwwDirPath, root)
			if err != nil {
				// Can't point a website symlink at a non-directory
				invalid = append(invalid, models.InvalidWebsite{
					Hosts: []string{vHost},
					Root:  root,
					Error: fmt.Errorf("Could not get rel of symlink: %w", err),
				})

				// Move to next website
				continue
			}

			if strings.Contains(rel, "../") {
				// Can't point a website symlink outside the www directory
				invalid = append(invalid, models.InvalidWebsite{
					Hosts: []string{vHost},
					Root:  root,
					Error: fmt.Errorf("Website symlink cannot point outside of %s/", p.wwwDirName),
				})

				// Move to next website
				continue
			}

			// Valid symlink
			websites[root] = &models.Website{
				Hosts: []string{vHost},
				Root:  root,
			}
		}
	}

	valid := make([]models.Website, 0)

	for _, v := range websites {
		valid = append(valid, *v)
	}

	return valid, invalid, nil
}
