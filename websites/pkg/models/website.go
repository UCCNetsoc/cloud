package websites

// WebsiteUserOpts User specified options for a websites
type WebsiteUserOpts struct {
	Host string `json:"host"`
	Path string `json:"path"`
}

// Website Website
type Website struct {
	WebsiteUserOpts
	User string `json:"user"`
}
