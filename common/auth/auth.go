package auth

import (
	"context"
	"fmt"
	"net/http"
	"strings"

	rest "common/rest"

	"github.com/dgrijalva/jwt-go"
	jwtauth "github.com/go-chi/jwtauth"
)

type Account struct {
	Username string
	Email    string
}

func NetsocAccountFromContext(ctx context.Context) (*Account, error) {
	_, claims, err := jwtauth.FromContext(ctx)
	if err != nil {
		return nil, err
	}

	if _, ok := claims["preferred_username"].(string); !ok {
		return nil, fmt.Errorf("jwt missing profile scope")
	}

	if _, ok := claims["email"].(string); !ok {
		return nil, fmt.Errorf("jwt missing email scope")
	}

	return &Account{
		Username: claims["preferred_username"].(string),
		Email:    claims["email"].(string),
	}, nil
}

func RequireNetsocAccountJWT(publicKeyText string, signingAlgorithm string) (func(next http.Handler) http.Handler, error) {
	return RequireKeycloakRoleJWT(publicKeyText, signingAlgorithm, "netsoc_account")
}

func RequireKeycloakRoleJWT(publicKeyText string, signingAlgorithm string, role string) (func(next http.Handler) http.Handler, error) {
	publicKey, err := jwt.ParseRSAPublicKeyFromPEM([]byte(publicKeyText))
	if err != nil {
		return nil, err
	}

	tokenAuth := jwtauth.New(signingAlgorithm, nil, publicKey)

	// The jwtauth middleware verifies that  JWT is present/valid signing
	// Since we want to abstract that away from the user, we're gonna call it inside this middleware
	verifier := jwtauth.Verifier(tokenAuth)

	return func(next http.Handler) http.Handler {
		return verifier(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			token, claims, err := jwtauth.FromContext(r.Context())

			if err != nil {
				rest.WriteError(w, 401, &rest.Detail{
					Msg: fmt.Sprintf("%s: %s", http.StatusText(401), err.Error()),
				})
				return
			}

			if token == nil || !token.Valid {
				rest.WriteError(w, 401, &rest.Detail{
					Msg: fmt.Sprintf("%s: %s", http.StatusText(401), "invalid token"),
				})
				return
			}

			var authorized bool = false

			if realmAccess, ok := claims["realm_access"]; ok {
				if roles, ok := realmAccess.(map[string]interface{})["roles"]; ok {
					for _, role := range roles.([]interface{}) {
						if role.(string) == role {
							authorized = true
						}
					}
				}
			} else {
				rest.WriteError(w, 401, &rest.Detail{
					Msg: fmt.Sprintf("%s: %s", http.StatusText(401), "missing keycloak realm_access"),
				})
				return
			}

			if !authorized {
				rest.WriteError(w, 401, &rest.Detail{
					Msg: fmt.Sprintf("%s: %s %s", http.StatusText(401), "missing keycloak role: %s", role),
				})
				return
			}

			fmt.Println(claims)
			if scopes, ok := claims["scopes"].(string); ok {
				for _, scope := range []string{"openid", "profile", "email"} {
					if !strings.Contains(scopes, "openid") {
						rest.WriteError(w, 401, &rest.Detail{
							Msg: fmt.Sprintf("%s: %s %s", http.StatusText(401), scope, "scope is required"),
						})
						return
					}
				}
			} else {
				rest.WriteError(w, 401, &rest.Detail{
					Msg: fmt.Sprintf("%s: %s %s", http.StatusText(401), "missing scopes"),
				})
				return
			}

			next.ServeHTTP(w, r)
		}))
	}, nil
}
