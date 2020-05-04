module common

go 1.14

replace common/rest => ./rest

require (
	github.com/dgrijalva/jwt-go v3.2.0+incompatible // indirect
	github.com/go-chi/chi v4.1.1+incompatible // indirect
	github.com/go-chi/jwtauth v4.0.4+incompatible // indirect
)
