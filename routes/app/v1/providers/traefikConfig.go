package traefikConfig

import (
	"fmt"
	consul "github.com/hashicorp/consul/api"
)

interface Config  {
	GetKV(key string) (string, error)
	GetKVs(keys string[]) (map[string]string, error)
	SetKV(key string, value) error
	SetKVs(kv map[string]string) error
}

type Consul struct {
	client *consul.Client
	rootKey string
}

func NewConsul(rootKey string) (*Consul, error) {
	client, err := consul.NewClient(api.DefaultConfig())
	if err != nil {
		return nil, err
	}

	return &Consul{
		client: client,
		rootKey: rootKey
	}, nil
}


func (p *Consul) GetKV(key string) (string, error) {
	kv := p.client.KV()

	pair, _, err := kv.Get(p.rootKey + "." + key)
	if err != nil {
		return nil, err
	}

	return pair.Value, nil
}

func (p *Consul) GetKVs(keys string[]) (map[string]string, error) {
	kv := make(map[string]string)

	for i, k := range keys {
		value, err := p.GetKV(k)

		if err != nil {
			return nil, err
		}
	}

	return kv, nil
}

func (p *Consul) SetKV(key string, value string) error {
	kv := p.client.KV()

	p := &consul.KVPair{Key: p.rootKey + "." + key, Value: []byte(value)}
	_, err := kv.Put(p, nil)

	if err != nil {
		return err
	}

	return nil
}

func (p *Consul) SetKVs(kv map[string]string) error {
	for k, v := range kv {
		err := p.SetKv(k,v)

		if err != nil {
			return err
		}
	}

	return nil
}

