package websites
package v1

type Detail struct {
	msg string		`json:"msg"`
	loc []string 	`json:"loc",omitempty`
}

type Error struct {
	detail Detail	`json:"detail"`
}

type Info struct {
	detail Detail	`json:"detail"`
}