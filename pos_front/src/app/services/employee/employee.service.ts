import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { ImportPossibleFields } from 'src/models/interfaces/importPossibleField';
import { baseUrl } from 'src/models/interfaces/baseURL';
import { baseOut} from 'src/models/interfaces/baseOut'
import { MatchyUploadEntry } from 'src/models/classes/MatchyUploadEntry';
//import { EmployeeFilter } from 'src/models/classes/employeeFilter'
@Injectable({
  providedIn: 'root'
})
export class EmployeeService {

  constructor(private http: HttpClient) { }

  getOptions(){
    const endPointUrl = baseUrl + 'employee/possibleFields';
    return this.http.get<ImportPossibleFields>();
  }

  upload(data: MatchyUploadEntry) {
    const endPointUrl = baseUrl + 'employee/test';
    this.http.post<baseOut>(endPointUrl, data);
  }
}
