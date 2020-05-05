package models

// Website represents a website with vhosts and root index directory
type Website struct {
	Hosts []string `json:"hosts"` // Array of virtual hosts that will serve this website
	Root  string   `root:"root"`  // The root path of the website index
}

// InvalidWebsite represents a website that is invalid in some fashion
// i.e the Hosts don't resolve, path doesn't exist, etc...
type InvalidWebsite struct {
	Hosts []string `json:"hosts"`
	Root  string   `json:"root"`
	Error error    `json:"error"`
}
