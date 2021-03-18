package com.example.snipee;
/*
Coord_filter.java
    implements moving average filter of size winSize
 */
import android.util.Log;

import java.util.LinkedList;

public class Coord_filter {
    private int winSize;
    private LinkedList<Float> bufferX;
    private LinkedList<Float> bufferY;

    public Coord_filter(int winSize){
        this.winSize = winSize;
        this.bufferX = new LinkedList<Float>();
        this.bufferY = new LinkedList<Float>();
        this.initBuffers();
    }

    public float[] getFilteredCoords(float xin, float yin){
        //insert current coords into buffer and get average
        this.shiftBuffers(xin, yin);
        float[] result = new float[2];
        result[0] = this.getAverageX();
        result[1] = this.getAverageY();
        return result;
    }

    public String toStringX(){
        //DEBUG ONLY
        StringBuilder s = new StringBuilder();
        for (float f: this.bufferX){
            s.append(f).append(", ");
        }
        s.append("\n");
        return s.toString();
    }

    public String toStringY(){
        //DEBUG ONLY
        StringBuilder s = new StringBuilder();
        for (float f: this.bufferY){
            s.append(f).append(", ");
        }
        s.append("\n");
        return s.toString();
    }

    private void initBuffers(){
        //fill linked list with winSize 0's
        for (int i=0; i<this.winSize; i++){
            this.bufferX.addLast((float)0);
            this.bufferY.addLast((float)0);
        }
    }

    private void shiftBuffers(float xin, float yin){
        //shift buffers right and insert xin,yin into first position
        this.bufferX.removeLast();
        this.bufferY.removeLast();
        this.bufferX.addFirst(xin);
        this.bufferY.addFirst(yin);
    }

    private float getAverageX() {
        //returns average of bufferX elements
        float sum = 0;
        for (float f: bufferX){
            sum += f;
        }
        return sum/this.winSize;
    }

    private float getAverageY() {
        //returns average of bufferX elements
        float sum = 0;
        for (float f: bufferY){
            sum += f;
        }
        return sum/this.winSize;
    }

}
