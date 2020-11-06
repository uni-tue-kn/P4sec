cmake_minimum_required(VERSION 3.5)
project(p4sec-externs VERSION 1.0.0)

# Dependencies
add_library(dependencies INTERFACE)

# - OpenSSL
find_package(OpenSSL REQUIRED)
target_link_libraries(dependencies INTERFACE OpenSSL::SSL OpenSSL::Crypto)

# - behavioral model
target_include_directories(dependencies INTERFACE /usr/local/include)
target_link_libraries(dependencies INTERFACE /usr/local/lib/libbmall.a)

# Modules
# - ipsec
add_library(p4ipsec MODULE p4ipsec.cpp)
set_target_properties(p4ipsec PROPERTIES CXX_STANDARD 14 CXX_STANDARD_REQUIRED YES)
target_link_libraries(p4ipsec PRIVATE dependencies)

# - macsec
add_library(p4macsec MODULE p4macsec.cpp)
set_target_properties(p4macsec PROPERTIES CXX_STANDARD 14 CXX_STANDARD_REQUIRED YES)
target_link_libraries(p4macsec PRIVATE dependencies)
