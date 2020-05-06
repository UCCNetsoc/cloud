package main

import (
	"flag"
	"time"

	providers "github.com/UCCNetsoc/nsa3/websites/pkg/providers"
)

func main() {
	control = flag.String("control", "/var/run/control.unit.sock", "Control socket of Nginx Unit (defaults to /var/run/control.unit.sock for the Docker release)")
	pollInterval := flag.Uint("interval", 4, "The number of seconds between home directory rescans")
	flag.Parse()

	prov, err := providers.MakeUserHomeDirWebsites(
		"./home/",
		"www",
		"netsoc.co",
		[]string{"84.39.234.51"},
		"nsa",
	)

	if err != nil {
		panic(err)
	}

	ticker := time.NewTicker(time.Duration(*pollInterval) * time.Second)
	quit := make(chan struct{})

	for {
		select {
		case <-ticker.C:
			valid, invalid, err := prov.List()

			for _, website := range valid {
				
			}
		case <-quit:
			ticker.Stop()
			return
		}
	}

}
