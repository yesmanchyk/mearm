rm -fr build
mkdir build
cd build
cmake ..
cmake --build .
./tests
cd ..

