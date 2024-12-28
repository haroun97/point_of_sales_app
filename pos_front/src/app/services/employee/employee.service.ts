import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { ImportPossibleFields } from 'src/models/classes/interfaces/importPossibleField';
import { baseUrl } from 'src/models/classes/interfaces/baseURL';
//import { EmployeeFilter } from 'src/models/classes/employeeFilter'
@Injectable({
  providedIn: 'root'
})
export class EmployeeService {

  constructor(private http: HttpClient) { }

  getOptions(){
    const endPointUrl = baseUrl + 'employee/possibleFields'
    return this.http.get<ImportPossibleFields>()
  }
}
