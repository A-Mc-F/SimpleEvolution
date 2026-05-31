def main():
    World_width = 10
    World_height = 10
    Resolution = 1

    Map_width = World_width*Resolution
    Map_height = World_height*Resolution

    Temperature_Map=[ [ 0 for i in range(Map_width) ] for j in range(Map_height) ]
    Marker_Map = [ [ 0 for i in range(Map_width) ] for j in range(Map_height) ]

    Temperature_Map[5][5]=1

    for x in range(10):
        print("-")
        for i in range(Map_height):
            print(Temperature_Map[i])

        '''   
        for i in range(Map_height):
            print(Marker_Map[i])
        '''
        for i in range(Map_height):
            for j in range(Map_width):
                if Temperature_Map[j][i] == 1:
                    Marker_Map[j][i] = 1

        for i in range(Map_height):
            for j in range(Map_width):
                if Marker_Map[j][i] == 1:
                    left = (j-1)%Map_width
                    right = (j+1)%Map_width
                    top = (i-1)%Map_height
                    bottom = (i+1)%Map_height
                    Temperature_Map[left][i] = 1
                    Temperature_Map[right][i] = 1
                    Temperature_Map[j][bottom] = 1
                    Temperature_Map[j][top] = 1
                    Temperature_Map[j][i] = 0
            
        Marker_Map = [ [ 0 for i in range(Map_width) ] for j in range(Map_height) ]





    

if __name__ == "__main__":
    main()