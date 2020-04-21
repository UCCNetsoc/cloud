package models

import (
	"fmt"
	"net"
	"context"
	"strings"
	"errors"
)

type VirtualHostUserOpts struct {
	Host		string `json:"host"`
	PathPrefix	string `json:"path_prefix"`
}

type VirtualHost interface {
	VirtualHostUserOpts
	DestinationServer		string
	AdditionalRequestHeaders	map[string]string
}

func (v *VirtualHostUserOpts) EnsureExclusivelyResolvesTo(testAddr string) error {
	addrs, err := net.LookupHost(v.Host)
	if err != nil {
		return err
	}

	if len(addrs) == 1 && strings.Compare(addrs[0], testAddr) {
		return nil
	}

	return errors.New(fmt.Sprinf("Host %s does not resolve to %s", v.Host, testAddr))
}


